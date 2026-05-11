import asyncio

from database import get_db
from model.lead import find_lead, create_lead, get_lead_collection
from lib.scrap.browserScrap import launch_browser
from lib.scrap.collectorScrap import collect_all_businesses
from lib.scrap.configScrap import SCRAPING_CONFIG
from lib.scrap.interfaceScrap import BusinessData, DatabaseCounter
from lib.scrap.navigationScrap import navigate_to_search
from lib.scrap.utilityScrap import pick_random
from lib.rf.interfaceML import PredictionInput
from lib.rf.predictorML import run_prediction

_active_jobs: dict[str, asyncio.Task] = {}


def register_job(job_id: str, task: asyncio.Task) -> None:
    _active_jobs[job_id] = task


def get_job(job_id: str) -> asyncio.Task | None:
    return _active_jobs.get(job_id)


def remove_job(job_id: str) -> None:
    _active_jobs.pop(job_id, None)


def list_jobs() -> list[dict]:
    return [{"job_id": jid, "done": task.done()} for jid, task in _active_jobs.items()]


async def _load_existing_names(db, location: str, keyword: str) -> set[str]:
    collection = get_lead_collection(db)
    docs       = await collection.find(
        {"lokasi": location, "keyword": keyword},
        {"nama": 1, "_id": 0},
    ).to_list(length=None)
    return {doc["nama"] for doc in docs if doc.get("nama")}


async def run_scrape_and_classify_job(
    job_id:   str,
    keyword:  str,
    location: str,
    target:   float,
    queue:    asyncio.Queue,
) -> None:
    db             = get_db()
    counter        = DatabaseCounter()
    browser_result = None

    def send(event_type: str, message: str) -> None:
        queue.put_nowait({"type": event_type, "message": message})

    try:
        target_label = "∞" if target == float("inf") else int(target)
        send("info", f"Memulai scraping: '{keyword}' di '{location}' | target: {target_label}")

        existing_names = await _load_existing_names(db, location, keyword)
        if existing_names:
            send("info", f"{len(existing_names)} data sudah ada di database dan akan dilewati.")

        user_agent     = pick_random(SCRAPING_CONFIG["USER_AGENTS"])
        browser_result = await launch_browser(user_agent)
        page           = browser_result.page

        search_query = f"{keyword} {location}"
        await navigate_to_search(page, search_query)
        send("info", f"Halaman Google Maps berhasil dimuat — query: '{search_query}'")

        async def on_extracted(item: BusinessData) -> None:
            await _save_item(db, item, location, keyword, send, counter)

        await collect_all_businesses(page, target, send, on_extracted, existing_names)

        send("info", f"Scraping selesai — tersimpan: {counter.saved}, dilewati: {counter.skipped}")
        send("info", "Memulai klasifikasi machine learning...")

        await classify_unprocessed(db, send)
        send("done", "Seluruh proses selesai.")

    except asyncio.CancelledError:
        send("info", f"Job {job_id} dibatalkan.")

    except Exception as err:
        send("error", f"Terjadi kesalahan: {err}")

    finally:
        if browser_result:
            await browser_result.browser.close()

        remove_job(job_id)
        queue.put_nowait(None)


async def _save_item(
    db,
    item:     BusinessData,
    location: str,
    category: str,
    send,
    counter:  DatabaseCounter,
) -> None:
    try:
        if await find_lead(db, item.business_name, location):
            counter.skipped += 1
            return

        await create_lead(db, {
            "nama":         item.business_name,
            "rating":       item.rating,
            "jumlahUlasan": item.review_count,
            "noTelp":       item.phone,
            "website":      item.website,
            "alamat":       item.address,
            "mapsUrl":      item.maps_url,
            "keterangan":   "",
            "status":       "Belum Diproses",
            "keyword":      category,
            "lokasi":       location,
        })

        counter.saved += 1
        send("success", f"Tersimpan: {item.business_name}")

    except Exception as err:
        send("error", f'Gagal menyimpan "{item.business_name}": {err}')


async def classify_unprocessed(db, send) -> None:
    collection = get_lead_collection(db)
    leads      = await collection.find(
        {"status": "Belum Diproses"},
        {"_id": 1, "rating": 1, "jumlahUlasan": 1, "website": 1},
    ).to_list(length=None)

    if not leads:
        send("info", "Tidak ada data dengan status 'Belum Diproses'.")
        return

    inputs = [
        PredictionInput(
            rating        = lead.get("rating") or 0,
            jumlah_ulasan = lead.get("jumlahUlasan") or 0,
            website       = 1 if lead.get("website") else 0,
        )
        for lead in leads
    ]

    results     = await asyncio.to_thread(run_prediction, inputs)
    prospek     = sum(1 for r in results if r.status == "Prospek")
    not_prospek = len(results) - prospek

    for lead, result in zip(leads, results):
        await collection.update_one({"_id": lead["_id"]}, {"$set": {"status": result.status}})

    send("success", f"Klasifikasi selesai — Prospek: {prospek}, Belum Prospek: {not_prospek}")