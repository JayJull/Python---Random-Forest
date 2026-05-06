import re

from playwright.async_api import Page

from lib.scrap.interfaceScrap import BusinessData
from lib.scrap.utilityScrap import (
    clean_text,
    parse_rating,
    parse_review_count,
    format_phone_number,
    looks_like_phone,
    looks_like_website,
)


async def _try_get_text(page: Page, *selectors: str, timeout: int = 2000) -> str:
    for selector in selectors:
        try:
            text = await page.locator(selector).first.inner_text(timeout=timeout)
            if text:
                return text
        except Exception:
            continue
    return ""


async def _try_get_attr(page: Page, selector: str, attr: str, timeout: int = 2000) -> str:
    try:
        value = await page.locator(selector).first.get_attribute(attr, timeout=timeout)
        return value or ""
    except Exception:
        return ""


def _assign_phone_or_website(data: BusinessData, raw_phone: str, raw_website: str) -> None:
    for field, value in {"phone": clean_text(raw_phone), "website": clean_text(raw_website)}.items():
        if not value:
            continue
        if looks_like_phone(value):
            data.phone = format_phone_number(value)
        elif looks_like_website(value):
            data.website = value
        elif field == "phone":
            data.phone = format_phone_number(value)
        elif field == "website":
            data.website = value


async def extract_business_details(page: Page) -> BusinessData | None:
    data = BusinessData()

    try:
        await page.wait_for_selector("h1.DUwDvf", timeout=5000)
    except Exception:
        return None

    try:
        current_url = page.url
        if "google.com/maps" in current_url:
            data.maps_url = current_url.split("?")[0] or current_url
    except Exception:
        pass

    name_text = await _try_get_text(page, "h1.DUwDvf", 'h1[class*="fontHeadline"]')
    if name_text:
        data.business_name = clean_text(name_text)

    category_text = await _try_get_text(page, 'button[jsaction*="category"]', 'button[class*="DkEaL"]')
    if category_text:
        data.category = clean_text(category_text)

    try:
        rating_text = await _try_get_text(page, 'div.F7nice span[aria-hidden="true"]', 'span.ceNzKf[aria-hidden="true"]')
        if rating_text:
            data.rating = parse_rating(rating_text)
    except Exception:
        pass

    try:
        review_text = await _try_get_text(page, 'div.F7nice span[aria-label*="ulasan"]')
        if review_text:
            data.review_count = parse_review_count(review_text)
    except Exception:
        pass

    address_text = await _try_get_text(page, 'button[data-item-id="address"]')
    if not address_text:
        address_text = await _try_get_attr(page, 'button[data-item-id*="address"]', "aria-label")
    if address_text:
        data.address = clean_text(address_text)

    raw_phone   = ""
    raw_website = ""

    try:
        phone_button = page.locator('button[data-item-id*="phone"]').first
        if await phone_button.count() > 0:
            data_id = await phone_button.get_attribute("data-item-id", timeout=2000)
            if data_id and ":" in data_id:
                raw_phone = data_id.split(":")[-1]
    except Exception:
        pass

    if not raw_phone:
        try:
            phone_button = page.locator('button[aria-label*="Telepon"]').first
            if await phone_button.count() > 0:
                aria_label = await phone_button.get_attribute("aria-label", timeout=1000) or ""
                match = re.search(r"[\d\s+\-()]+", aria_label)
                if match:
                    raw_phone = match.group(0)
        except Exception:
            pass

    try:
        raw_website = await _try_get_attr(page, 'a[data-item-id="authority"]', "href")
    except Exception:
        pass

    if not raw_website:
        try:
            raw_website = await _try_get_attr(page, 'a[aria-label*="Situs"]', "href")
        except Exception:
            pass

    _assign_phone_or_website(data, raw_phone, raw_website)

    if not data.phone:
        return None

    return data