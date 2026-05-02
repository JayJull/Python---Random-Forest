from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, IndexModel


def get_lead_collection(db) -> AsyncIOMotorCollection:
    return db["leads"]


async def ensure_indexes(db) -> None:
    collection = get_lead_collection(db)
    await collection.create_indexes([
        IndexModel([("nama", ASCENDING), ("lokasi", ASCENDING)], unique=True),
    ])


async def find_lead(db, nama: str, lokasi: str) -> Optional[dict]:
    return await get_lead_collection(db).find_one({"nama": nama, "lokasi": lokasi})


async def create_lead(db, data: dict) -> None:
    payload = {**data, "createdAt": datetime.now(timezone.utc)}
    await get_lead_collection(db).insert_one(payload)


async def get_all_leads(
    db,
    lokasi:  Optional[str] = None,
    keyword: Optional[str] = None,
    status:  Optional[str] = None,
    skip:    int = 0,
    limit:   int = 100,
) -> list[dict]:
    query: dict = {}

    if lokasi:
        query["lokasi"] = lokasi
    if keyword:
        query["keyword"] = keyword
    if status:
        query["status"] = status

    cursor = get_lead_collection(db).find(query, {"_id": 0}).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def count_leads(
    db,
    lokasi:  Optional[str] = None,
    keyword: Optional[str] = None,
    status:  Optional[str] = None,
) -> int:
    query: dict = {}

    if lokasi:
        query["lokasi"] = lokasi
    if keyword:
        query["keyword"] = keyword
    if status:
        query["status"] = status

    return await get_lead_collection(db).count_documents(query)