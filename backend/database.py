from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import MONGODB_DB, MONGODB_URI

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[MONGODB_DB]


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
