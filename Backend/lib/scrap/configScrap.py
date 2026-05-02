from typing import Final

SCRAPING_CONFIG: Final[dict] = {
    "MODE_HEADLESS":         True,
    "VIEWPORT_WIDTH":        1920,
    "VIEWPORT_HEIGHT":       1080,
    "MAX_SCROLL_ATTEMPTS":   80,
    "MAX_CONSECUTIVE_FAILS": 5,
    "SCROLL_DELAY_MIN_MS":   1200,
    "SCROLL_DELAY_MAX_MS":   2500,
    "CLICK_DELAY_MIN_MS":    1500,
    "CLICK_DELAY_MAX_MS":    2500,
    "MAX_DATA_PER_SESSION":  float("inf"),
    "USER_AGENTS": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ],
}