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


_WEBSITE_KEYWORDS = (
    "http", "www.", ".com", ".id", ".net", ".org", ".co.",
    ".io", "://", "lynkid", "bit.ly", "linktr", "instagram",
    "facebook", "tokopedia", "shopee", "gofood", "grab",
)

_PHONE_PATTERN = re.compile(r"^(\+?62|0)[0-9]{7,14}$")

_WEBSITE_PREFIX   = re.compile(r"^(https?://|www\.)", re.IGNORECASE)
_WEBSITE_TLD      = re.compile(
    r"\.(com|id|net|org|co\.id|io|ly|me|info|biz|web\.id|my\.id|ac\.id|go\.id|sch\.id|or\.id)(/|$)",
    re.IGNORECASE,
)
_WEBSITE_PLATFORM = re.compile(
    r"(lynkid|linktr\.ee|linktree|bit\.ly|s\.id|beacons\.ai|taplink|carrd\.co)",
    re.IGNORECASE,
)


def looks_like_phone(text: str) -> bool:
    if not text or any(kw in text for kw in _WEBSITE_KEYWORDS):
        return False
    return bool(_PHONE_PATTERN.match(re.sub(r"[\s\-().+]", "", text)))


def looks_like_website(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    return bool(
        _WEBSITE_PREFIX.match(t)
        or _WEBSITE_TLD.search(t)
        or _WEBSITE_PLATFORM.search(t)
    )


def format_phone_number(raw: str) -> str:
    if not raw:
        return ""
    clean = re.sub(r"[^\d+]", "", raw)
    if clean.startswith("+62"):
        return clean[1:]
    if clean.startswith("62"):
        return clean
    if clean.startswith("0"):
        return "62" + clean[1:]
    return "62" + clean