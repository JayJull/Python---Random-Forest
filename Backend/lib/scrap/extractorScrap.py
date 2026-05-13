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

_SKIP_DOMAINS = ("google.com", "goo.gl", "maps.app", "support.google")


async def _get_text(page: Page, *selectors: str, timeout: int = 2000) -> str:
    for selector in selectors:
        try:
            text = await page.locator(selector).first.inner_text(timeout=timeout)
            if text:
                return text
        except Exception:
            pass
    return ""


async def _get_attr(page: Page, selector: str, attr: str, timeout: int = 2000) -> str:
    try:
        return await page.locator(selector).first.get_attribute(attr, timeout=timeout) or ""
    except Exception:
        return ""


async def _collect_phone_candidates(page: Page) -> list[str]:
    candidates: list[str] = []

    try:
        for btn in await page.locator('button[data-item-id*="phone"]').all():
            data_id = await btn.get_attribute("data-item-id", timeout=1500)
            if data_id and ":" in data_id:
                number = data_id.split(":")[-1].strip()
                if number:
                    candidates.append(number)
    except Exception:
        pass

    if not candidates:
        try:
            for kw in ("Telepon", "Phone", "Call", "Hubungi"):
                for btn in await page.locator(f'button[aria-label*="{kw}"]').all():
                    aria = await btn.get_attribute("aria-label", timeout=1000) or ""
                    for m in re.findall(r"[\d\s\+\-\(\)\.]{6,}", aria):
                        if m.strip():
                            candidates.append(m.strip())
        except Exception:
            pass

    if not candidates:
        try:
            for link in await page.locator('a[href^="tel:"]').all():
                href = await link.get_attribute("href", timeout=1000) or ""
                number = href.replace("tel:", "").strip()
                if number:
                    candidates.append(number)
        except Exception:
            pass

    if not candidates:
        try:
            for el in await page.locator('[data-item-id]').all():
                text = (await el.inner_text(timeout=800)).strip()
                match = re.search(r"(\+?62|0)[0-9]{7,14}", text)
                if match:
                    candidates.append(match.group(0))
        except Exception:
            pass

    return candidates


async def _collect_website_candidates(page: Page) -> list[str]:
    candidates: list[str] = []

    href = await _get_attr(page, 'a[data-item-id="authority"]', "href")
    if href:
        candidates.append(href)

    if not candidates:
        try:
            for kw in ("Situs", "Website", "Web", "Kunjungi"):
                for link in await page.locator(f'a[aria-label*="{kw}"]').all():
                    href = await link.get_attribute("href", timeout=1000) or ""
                    if href and not any(d in href for d in _SKIP_DOMAINS):
                        candidates.append(href)
        except Exception:
            pass

    if not candidates:
        try:
            for link in await page.locator('a[href^="http"]').all():
                href = await link.get_attribute("href", timeout=800) or ""
                if href and not any(d in href for d in _SKIP_DOMAINS):
                    candidates.append(href)
                    break
        except Exception:
            pass

    return candidates


def _assign_contacts(
    data:               BusinessData,
    phone_candidates:   list[str],
    website_candidates: list[str],
) -> None:
    all_candidates = (
        [(v, "phone")   for v in phone_candidates   if v] +
        [(v, "website") for v in website_candidates if v]
    )

    for raw, hint in all_candidates:
        v = clean_text(raw)

        if looks_like_phone(v):
            if not data.phone:
                data.phone = format_phone_number(v)
        elif looks_like_website(v):
            if not data.website:
                data.website = v
        elif hint == "phone" and not data.phone:
            data.phone = format_phone_number(v)
        elif hint == "website" and not data.website:
            data.website = v


async def extract_business_details(page: Page) -> BusinessData:
    data = BusinessData()

    try:
        await page.wait_for_selector("h1.DUwDvf", timeout=5000)
    except Exception:
        return data

    try:
        url = page.url
        if "google.com/maps" in url:
            data.maps_url = url.split("?")[0] or url
    except Exception:
        pass

    name = await _get_text(page, "h1.DUwDvf", 'h1[class*="fontHeadline"]')
    if name:
        data.business_name = clean_text(name)

    category = await _get_text(page, 'button[jsaction*="category"]', 'button[class*="DkEaL"]')
    if category:
        data.category = clean_text(category)

    rating_text = await _get_text(
        page,
        'div.F7nice span[aria-hidden="true"]',
        'span.ceNzKf[aria-hidden="true"]',
    )
    if rating_text:
        data.rating = parse_rating(rating_text)

    review_text = await _get_text(
        page,
        'div.F7nice span[aria-label*="ulasan"]',
        'div.F7nice span[aria-label*="review"]',
    )
    if review_text:
        data.review_count = parse_review_count(review_text)

    address = await _get_text(page, 'button[data-item-id="address"]')
    if not address:
        address = await _get_attr(page, 'button[data-item-id*="address"]', "aria-label")
    if address:
        data.address = clean_text(address)

    phone_candidates   = await _collect_phone_candidates(page)
    website_candidates = await _collect_website_candidates(page)
    _assign_contacts(data, phone_candidates, website_candidates)

    return data