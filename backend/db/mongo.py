import os
from motor.motor_asyncio import AsyncIOMotorClient

_client = None
_db = None


def connect_to_mongo() -> None:
    global _client, _db
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME", "smartstudyplanner")

    if not mongo_uri:
        raise RuntimeError("MONGODB_URI is not set")

    _client = AsyncIOMotorClient(mongo_uri)
    _db = _client[db_name]


def close_mongo_connection() -> None:
    global _client, _db
    if _client:
        _client.close()
    _client = None
    _db = None


def get_db():
    if _db is None:
        raise RuntimeError("MongoDB not initialized")
    return _db
