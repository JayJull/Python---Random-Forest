import asyncio
import random
import re


async def wait(ms: int) -> None:
    await asyncio.sleep(ms / 1000)


async def random_delay(min_ms: int, max_ms: int) -> None:
    await wait(random.randint(min_ms, max_ms))


def pick_random(items: list):
    return random.choice(items)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).replace("\n", " ").replace("\r", " ").strip()


def parse_rating(text: str) -> float:
    try:
        return float(text.split()[0].replace(",", "."))
    except (ValueError, IndexError):
        return 0.0


def parse_review_count(text: str) -> int:
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else 0


def looks_like_phone(text: str) -> bool:
    cleaned = re.sub(r"[\s\-().+]", "", text)
    return bool(re.match(r"^(0[0-9]{8,12}|62[0-9]{8,12}|\+62[0-9]{8,12})$", cleaned))


def looks_like_website(text: str) -> bool:
    return bool(re.match(r"^(https?://|www\.)", text.strip(), re.IGNORECASE))


def format_phone_number(raw: str) -> str:
    if not raw:
        return ""
    clean = re.sub(r"[^\d+]", "", raw)
    if clean.startswith("0"):
        return "62" + clean[1:]
    if not clean.startswith("+") and not clean.startswith("62"):
        return "62" + clean
    return clean