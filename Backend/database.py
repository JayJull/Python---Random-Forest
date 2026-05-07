import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://appinersia:inersia123@localhost:27017/inersiaDB?authSource=InersiaDB")
        _client   = AsyncIOMotorClient(mongo_uri)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    db_name = os.getenv("MONGODB_DB", "inersiaDB")
    return get_client()[db_name]


async def close_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None