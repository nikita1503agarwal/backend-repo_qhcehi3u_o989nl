from pymongo import MongoClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from typing import Union
from pydantic import BaseModel

load_dotenv()

_client = None
db = None

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

if DATABASE_URL and DATABASE_NAME:
    _client = MongoClient(DATABASE_URL)
    db = _client[DATABASE_NAME]


def _ensure_db():
    if db is None:
        raise Exception("Database not available. Set DATABASE_URL and DATABASE_NAME.")


def create_document(collection_name: str, data: Union[BaseModel, dict]):
    _ensure_db()
    if isinstance(data, BaseModel):
        data = data.model_dump()
    doc = {**data}
    now = datetime.now(timezone.utc)
    doc.setdefault("created_at", now)
    doc["updated_at"] = now
    res = db[collection_name].insert_one(doc)
    return str(res.inserted_id)


def get_documents(collection_name: str, filter_dict: dict | None = None, limit: int | None = None):
    _ensure_db()
    cur = db[collection_name].find(filter_dict or {}).sort("updated_at", -1)
    if limit:
        cur = cur.limit(limit)
    return list(cur)


def get_document(collection_name: str, _id):
    _ensure_db()
    from bson import ObjectId
    return db[collection_name].find_one({"_id": ObjectId(_id)})


def update_document(collection_name: str, _id, data: dict):
    _ensure_db()
    from bson import ObjectId
    data["updated_at"] = datetime.now(timezone.utc)
    db[collection_name].update_one({"_id": ObjectId(_id)}, {"$set": data})
    return True


def delete_document(collection_name: str, _id):
    _ensure_db()
    from bson import ObjectId
    db[collection_name].delete_one({"_id": ObjectId(_id)})
    return True
