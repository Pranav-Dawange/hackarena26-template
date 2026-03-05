"""
utils/helpers.py — Shared Utility Functions
--------------------------------------------
Small, stateless helpers used across routes and services.
"""

from datetime import datetime, timezone
from bson import ObjectId
import json


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    """Return current UTC time as an ISO-8601 string."""
    return utcnow().isoformat()


class MongoJSONEncoder(json.JSONEncoder):
    """
    Extends the default JSON encoder to serialise types that PyMongo
    returns (ObjectId, datetime) into JSON-safe strings.
    """

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def serialize_doc(doc: dict) -> dict:
    """
    Convert a MongoDB document to a JSON-safe dict.
    Renames '_id' → 'id' and stringifies ObjectIds / datetimes.
    """
    if doc is None:
        return {}
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return json.loads(json.dumps(doc, cls=MongoJSONEncoder))


def serialize_docs(docs) -> list:
    """Serialize a cursor or list of MongoDB documents."""
    return [serialize_doc(d) for d in docs]


def paginate(collection, query: dict, page: int, per_page: int, sort_field: str = "timestamp", sort_dir: int = -1) -> dict:
    """
    Return a paginated result set from a MongoDB collection.

    Returns
    -------
    dict with keys: data, page, per_page, total
    """
    total = collection.count_documents(query)
    cursor = (
        collection.find(query)
        .sort(sort_field, sort_dir)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )
    return {
        "data":     serialize_docs(cursor),
        "page":     page,
        "per_page": per_page,
        "total":    total,
    }
