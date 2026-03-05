"""
models/event_model.py — Network Event Schema & Operations
----------------------------------------------------------
The `events` collection acts as an append-only audit / event log for the
mesh network.  Both automatic (alert service) and manual entries land here.

events document shape
----------------------
{
    "timestamp":  <datetime UTC>,
    "event_type": "NODE_OFFLINE",     # see EVENT_TYPES below
    "node_id":    "NODE-001",         # null for system-level events
    "severity":   "critical",         # "info" | "warning" | "critical"
    "message":    "Node has not sent a heartbeat for 90 seconds",
    "resolved":   false,              # cleared by the dashboard operator
}
"""

from pymongo.collection import Collection
from utils.helpers import utcnow, serialize_docs, paginate

# ── Allowed event types ───────────────────────────────────────────────────────
EVENT_TYPES = {
    "NODE_OFFLINE",
    "NODE_ONLINE",
    "NODE_DEGRADED",
    "REROUTE",
    "HIGH_PACKET_LOSS",
    "WEAK_SIGNAL",
    "DEAD_ZONE_DETECTED",
    "SYSTEM",
}

VALID_SEVERITIES = {"info", "warning", "critical"}


def log_event(
    collection: Collection,
    event_type: str,
    message: str,
    node_id: str | None = None,
    severity: str = "info",
) -> str:
    """
    Append an event to the events collection.  Returns inserted _id string.
    """
    doc = {
        "timestamp":  utcnow(),
        "event_type": event_type if event_type in EVENT_TYPES else "SYSTEM",
        "node_id":    node_id,
        "severity":   severity if severity in VALID_SEVERITIES else "info",
        "message":    message,
        "resolved":   False,
    }
    result = collection.insert_one(doc)
    return str(result.inserted_id)


def get_recent_events(
    collection: Collection,
    page: int = 1,
    per_page: int = 50,
    node_id: str | None = None,
    severity: str | None = None,
) -> dict:
    """Return paginated events, with optional filters on node_id and severity."""
    query: dict = {}
    if node_id:
        query["node_id"] = node_id
    if severity:
        query["severity"] = severity
    return paginate(collection, query, page, per_page, sort_field="timestamp", sort_dir=-1)


def resolve_event(collection: Collection, event_id_str: str) -> bool:
    """Mark an event as resolved.  Returns True if found."""
    from bson import ObjectId
    result = collection.update_one(
        {"_id": ObjectId(event_id_str)},
        {"$set": {"resolved": True}},
    )
    return result.matched_count > 0
