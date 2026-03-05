"""
models/node_model.py — Node Document Schema & Operations
----------------------------------------------------------
Defines the shape of a `nodes` collection document and provides
lightweight CRUD helpers used by services and routes.

nodes document shape
--------------------
{
    "node_id":       "NODE-001",          # unique string identifier
    "location":      "Building A Floor 2",
    "status":        "online",            # "online" | "offline" | "degraded"
    "last_seen":     <datetime UTC>,
    "battery_level": 87,                  # percentage, null if powered
    "ip_address":    "192.168.4.2",       # current mesh IP (optional)
    "hop_count":     2,                   # hops to root gateway
    "created_at":    <datetime UTC>,
}
"""

from datetime import datetime, timezone
from pymongo.collection import Collection
from utils.helpers import utcnow, serialize_doc, serialize_docs


# ── Allowed field values ───────────────────────────────────────────────────────
VALID_STATUSES = {"online", "offline", "degraded"}


def validate_node(data: dict) -> tuple[bool, str]:
    """
    Validate incoming node registration payload.

    Returns
    -------
    (True, "") on success, (False, error_message) on failure.
    """
    required = {"node_id", "location"}
    missing  = required - data.keys()
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    if "status" in data and data["status"] not in VALID_STATUSES:
        return False, f"'status' must be one of {VALID_STATUSES}"

    if "battery_level" in data and data["battery_level"] is not None:
        if not (0 <= int(data["battery_level"]) <= 100):
            return False, "'battery_level' must be between 0 and 100"

    return True, ""


def create_node(collection: Collection, data: dict) -> dict:
    """
    Insert a new node document.  Returns the created document.
    Raises DuplicateKeyError if node_id already exists.
    """
    doc = {
        "node_id":       data["node_id"],
        "location":      data["location"],
        "status":        data.get("status", "online"),
        "last_seen":     utcnow(),
        "battery_level": data.get("battery_level"),
        "ip_address":    data.get("ip_address"),
        "hop_count":     data.get("hop_count", 0),
        "created_at":    utcnow(),
    }
    result = collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize_doc(doc)


def get_all_nodes(collection: Collection) -> list:
    """Return all node documents."""
    return serialize_docs(collection.find())


def get_node_by_id(collection: Collection, node_id: str) -> dict | None:
    """Return a single node by its node_id, or None."""
    doc = collection.find_one({"node_id": node_id})
    return serialize_doc(doc) if doc else None


def update_node_heartbeat(collection: Collection, node_id: str, extra: dict = None) -> bool:
    """
    Update last_seen timestamp and any optional extra fields.
    Returns True if the document was found and updated.
    """
    update_fields = {"last_seen": utcnow()}
    if extra:
        update_fields.update(extra)

    result = collection.update_one(
        {"node_id": node_id},
        {"$set": update_fields},
    )
    return result.matched_count > 0


def set_node_status(collection: Collection, node_id: str, status: str) -> bool:
    """Update a node's status field.  Returns True on success."""
    result = collection.update_one(
        {"node_id": node_id},
        {"$set": {"status": status, "last_seen": utcnow()}},
    )
    return result.matched_count > 0
