from urllib.parse import quote
from playwright.async_api import Page
from lib.scrap.configScrap import SCRAPING_CONFIG
from lib.scrap.interfaceScrap import SendFn
from lib.scrap.utilityScrap import random_delay, wait

FEED_SELECTOR = 'div[role="feed"]'


async def navigate_to_search(page: Page, query: str) -> None:
    await page.goto(
        f"https://www.google.com/maps/search/{quote(query)}",
        wait_until="domcontentloaded",
    )
    await random_delay(3000, 5000)


async def scroll_results_panel(
    page:        Page,
    max_scrolls: int,
    target:      float,
    send:        SendFn,
) -> None:
    await page.wait_for_selector(FEED_SELECTOR, timeout=10000)

    previous_height  = 0
    scroll_count     = 0
    unchanged_streak = 0

    while scroll_count < max_scrolls:
        await page.evaluate(f"""
            const el = document.querySelector('{FEED_SELECTOR}');
            if (el) el.scrollTo(0, el.scrollHeight);
        """)

        await random_delay(
            SCRAPING_CONFIG["SCROLL_DELAY_MIN_MS"],
            SCRAPING_CONFIG["SCROLL_DELAY_MAX_MS"],
        )

        current_height: int = await page.evaluate(f"""
            const el = document.querySelector('{FEED_SELECTOR}');
            el ? el.scrollHeight : 0;
        """)

        if current_height == previous_height:
            unchanged_streak += 1
            if unchanged_streak >= 3:
                send("info", "Telah mencapai akhir hasil pencarian.")
                break
        else:
            unchanged_streak = 0

        previous_height = current_height
        scroll_count   += 1

        visible = await page.locator('a[href*="/maps/place/"]').count()
        send("loading", f"Scroll ke-{scroll_count} dari {max_scrolls} — item terlihat: {visible}")

        if target != float("inf") and visible >= target + 10:
            send("info", f"Item yang dimuat sudah cukup untuk target {int(target)} data. Scroll dihentikan.")
            break


async def go_back_to_list(page: Page) -> None:
    try:
        back_button = page.locator('button[aria-label*="Kembali"], button[aria-label*="Back"]').first
        if await back_button.count() > 0:
            await back_button.click()
            await wait(500)
            return
    except Exception:
        pass

    try:
        feed = page.locator(FEED_SELECTOR).first
        if await feed.count() > 0:
            await feed.click()
            await wait(500)
            return
    except Exception:
        pass

    try:
        await page.keyboard.press("Escape")
        await wait(500)
    except Exception:
        pass