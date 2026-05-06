from database import get_db
from services.scrapService import classify_unprocessed


async def run_classify() -> list[str]:
    db  = get_db()
    log: list[str] = []

    await classify_unprocessed(db, lambda event_type, msg: log.append(f"[{event_type}] {msg}"))
    return log