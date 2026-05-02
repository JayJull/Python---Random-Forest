from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from lib.scrap.configScrap import SCRAPING_CONFIG


@dataclass
class BrowserResult:
    browser: Browser
    page:    Page


async def launch_browser(user_agent: str) -> BrowserResult:
    playwright = await async_playwright().start()

    browser: Browser = await playwright.chromium.launch(
        headless=SCRAPING_CONFIG["MODE_HEADLESS"],
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
    )

    context: BrowserContext = await browser.new_context(
        viewport={
            "width":  SCRAPING_CONFIG["VIEWPORT_WIDTH"],
            "height": SCRAPING_CONFIG["VIEWPORT_HEIGHT"],
        },
        user_agent=user_agent,
        locale="id-ID",
        timezone_id="Asia/Jakarta",
        has_touch=False,
        is_mobile=False,
        java_script_enabled=True,
    )

    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins',   { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['id-ID', 'id', 'en-US', 'en'] });

        window.chrome = { runtime: {} };

        const originalQuery = window.navigator.permissions.query.bind(window.navigator.permissions);
        window.navigator.permissions.query = (parameter) =>
            parameter.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameter);
    """)

    page: Page = await context.new_page()
    page.set_default_timeout(60000)

    return BrowserResult(browser=browser, page=page)