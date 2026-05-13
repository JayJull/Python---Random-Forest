from typing import Callable, Awaitable

from playwright.async_api import Page

from lib.scrap.configScrap import SCRAPING_CONFIG
from lib.scrap.extractorScrap import extract_business_details
from lib.scrap.interfaceScrap import BusinessData, SendFn
from lib.scrap.navigationScrap import go_back_to_list, scroll_results_panel
from lib.scrap.utilityScrap import random_delay

PLACE_LINK_SELECTOR = 'a[href*="/maps/place/"]'
FEED_SELECTOR       = 'div[role="feed"]'


async def collect_all_businesses(
    page:           Page,
    target:         float,
    send:           SendFn,
    on_extracted:   Callable[[BusinessData], Awaitable[None]],
    existing_names: set[str] = None,
) -> list[BusinessData]:
    results:        list[BusinessData] = []
    seen_names:     set[str]           = set(existing_names or [])
    failed_indices: set[int]           = set()
    current_index                      = 0
    consecutive_fails                  = 0
    skipped_no_phone                   = 0

    while len(results) < target:
        try:
            await page.wait_for_selector(FEED_SELECTOR, timeout=5000)

            links       = await page.locator(PLACE_LINK_SELECTOR).all()
            total_links = len(links)

            if total_links == 0:
                send("info", "Tidak ada daftar bisnis yang ditemukan.")
                break

            if current_index >= total_links:
                send("loading", f"Memuat lebih banyak hasil (indeks saat ini: {current_index})...")
                await scroll_results_panel(
                    page,
                    10,
                    float("inf") if target == float("inf") else target,
                    send,
                )
                links       = await page.locator(PLACE_LINK_SELECTOR).all()
                total_links = len(links)

                if current_index >= total_links:
                    send("info", "Tidak ada data lagi yang tersedia.")
                    break

            if current_index in failed_indices:
                current_index += 1
                continue

            target_label = "∞" if target == float("inf") else int(target)
            send("info", f"Memproses item ke-{current_index + 1} dari {total_links} — terkumpul: {len(results)} dari {target_label}")

            links = await page.locator(PLACE_LINK_SELECTOR).all()
            if current_index >= len(links):
                current_index += 1
                continue

            await links[current_index].click()
            await random_delay(
                SCRAPING_CONFIG["CLICK_DELAY_MIN_MS"],
                SCRAPING_CONFIG["CLICK_DELAY_MAX_MS"],
            )

            business = await extract_business_details(page)

            if not business.business_name:
                consecutive_fails += 1
                failed_indices.add(current_index)
                await go_back_to_list(page)
                current_index += 1
                continue

            if not business.phone:
                skipped_no_phone += 1
                send("info", f"Dilewati (tidak ada nomor telepon): {business.business_name}")
                failed_indices.add(current_index)
                await go_back_to_list(page)
                current_index += 1
                continue

            if business.business_name in seen_names:
                failed_indices.add(current_index)
                await go_back_to_list(page)
                current_index += 1
                continue

            seen_names.add(business.business_name)
            results.append(business)
            consecutive_fails = 0

            result_label = "∞" if target == float("inf") else str(int(target))
            website_info = f" | 🌐 {business.website}" if business.website else ""
            send(
                "success",
                f"[{len(results)}/{result_label}] {business.business_name}"
                f" — ☎ {business.phone}{website_info}"
                f" | ⭐ {business.rating} ({business.review_count} ulasan)",
            )

            await on_extracted(business)
            await go_back_to_list(page)
            await random_delay(500, 1000)

            current_index += 1

        except Exception as err:
            send("error", f"Gagal memproses indeks {current_index}: {err}")
            consecutive_fails += 1
            failed_indices.add(current_index)

            try:
                await go_back_to_list(page)
            except Exception:
                pass

            current_index += 1

            if consecutive_fails >= SCRAPING_CONFIG["MAX_CONSECUTIVE_FAILS"]:
                send("info", f"Proses dihentikan — {consecutive_fails} kegagalan berturutan.")
                break

    if skipped_no_phone:
        send("info", f"Total dilewati karena tidak ada nomor telepon: {skipped_no_phone}")

    return results