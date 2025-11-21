import os
from typing import Any, Dict, List
from datetime import datetime
from pymongo import MongoClient

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "dear_diary")

_client = MongoClient(DATABASE_URL)
db = _client[DATABASE_NAME]

# Helpers

def _now():
    return datetime.utcnow()


def create_document(collection_name: str, data: Dict[str, Any]) -> str:
    doc = {**data, "created_at": data.get("created_at") or _now(), "updated_at": data.get("updated_at") or _now()}
    res = db[collection_name].insert_one(doc)
    return str(res.inserted_id)


def update_document(collection_name: str, doc_id, data: Dict[str, Any]):
    from bson import ObjectId
    db[collection_name].update_one({"_id": ObjectId(doc_id)}, {"$set": {**data, "updated_at": _now()}})


def get_documents(collection_name: str, filter_dict: Dict[str, Any] | None = None, limit: int | None = None) -> List[Dict[str, Any]]:
    cursor = db[collection_name].find(filter_dict or {}).sort("updated_at", -1)
    if limit:
        cursor = cursor.limit(limit)
    out = []
    for d in cursor:
        d["_id"] = str(d["_id"])  # serialize
        out.append(d)
    return out


def get_document(collection_name: str, doc_id: str) -> Dict[str, Any] | None:
    from bson import ObjectId
    d = db[collection_name].find_one({"_id": ObjectId(doc_id)})
    if not d:
        return None
    d["_id"] = str(d["_id"])  # serialize
    return d


def delete_document(collection_name: str, doc_id: str) -> bool:
    from bson import ObjectId
    res = db[collection_name].delete_one({"_id": ObjectId(doc_id)})
    return res.deleted_count > 0
