from bson import ObjectId

from database import get_db
from model.lead import count_leads, get_all_leads
from services.scrapService import classify_unprocessed


async def get_leads(
    lokasi:  str | None,
    keyword: str | None,
    status:  str | None,
    skip:    int,
    limit:   int,
) -> dict:
    db    = get_db()
    total = await count_leads(db, lokasi, keyword, status)
    data  = await get_all_leads(db, lokasi, keyword, status, skip, limit)
    return {"total": total, "skip": skip, "limit": limit, "data": data}


async def get_leads_stats() -> dict:
    db         = get_db()
    total      = await count_leads(db)
    all_status = ["Belum Diproses", "Prospek", "Belum Prospek"]
    by_status  = {s: await count_leads(db, status=s) for s in all_status}
    return {"total": total, "by_status": by_status}


async def run_classify() -> list[str]:
    db  = get_db()
    log: list[str] = []

    await classify_unprocessed(db, lambda event_type, msg: log.append(f"[{event_type}] {msg}"))
    return log


async def delete_lead(lead_id: str) -> bool:
    db = get_db()
    try:
        oid = ObjectId(lead_id)
    except Exception:
        return False

    result = await db["leads"].delete_one({"_id": oid})
    return result.deleted_count > 0


async def update_lead(lead_id: str, payload: dict) -> bool:
    db = get_db()
    try:
        oid = ObjectId(lead_id)
    except Exception:
        return False

    result = await db["leads"].update_one({"_id": oid}, {"$set": payload})
    return result.matched_count > 0