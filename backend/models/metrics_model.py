"""
models/metrics_model.py — Network Metrics Schema & Operations
--------------------------------------------------------------
Handles the `metrics` and `sensor_data` MongoDB collections.

metrics document shape
-----------------------
{
    "timestamp":   <datetime UTC>,
    "node_id":     "NODE-001",
    "rssi":        -65,          # dBm (negative integer)
    "latency_ms":  12,           # milliseconds
    "packet_loss": 2.5,          # percentage float 0–100
    "throughput":  48.3,         # kbps (optional)
}

sensor_data document shape
---------------------------
{
    "timestamp":   <datetime UTC>,
    "node_id":     "NODE-001",
    "temperature": 28.4,         # Celsius
    "humidity":    62.1,         # percent RH
}
"""

from pymongo.collection import Collection
from utils.helpers import utcnow, serialize_docs, paginate


# ── Validation ─────────────────────────────────────────────────────────────────
def validate_metrics(data: dict) -> tuple[bool, str]:
    required = {"node_id", "rssi"}
    missing  = required - data.keys()
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    if not (-120 <= int(data["rssi"]) <= 0):
        return False, "'rssi' must be a value between -120 and 0 dBm"

    if "packet_loss" in data and not (0.0 <= float(data["packet_loss"]) <= 100.0):
        return False, "'packet_loss' must be between 0 and 100"

    return True, ""


def validate_sensor_data(data: dict) -> tuple[bool, str]:
    required = {"node_id", "temperature", "humidity"}
    missing  = required - data.keys()
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, ""


# ── Metrics CRUD ───────────────────────────────────────────────────────────────
def insert_metrics(collection: Collection, data: dict) -> str:
    """Insert a network metrics document.  Returns the inserted _id as string."""
    doc = {
        "timestamp":   utcnow(),
        "node_id":     data["node_id"],
        "rssi":        int(data["rssi"]),
        "latency_ms":  int(data.get("latency_ms", 0)),
        "packet_loss": float(data.get("packet_loss", 0.0)),
        "throughput":  float(data.get("throughput", 0.0)),
    }
    result = collection.insert_one(doc)
    return str(result.inserted_id)


def get_metrics_history(
    collection: Collection,
    node_id: str | None,
    page: int,
    per_page: int,
) -> dict:
    """Return paginated metrics, optionally filtered by node_id."""
    query = {"node_id": node_id} if node_id else {}
    return paginate(collection, query, page, per_page, sort_field="timestamp", sort_dir=-1)


def get_latest_metrics_per_node(collection: Collection) -> list:
    """
    Return the most recent metrics document for every node.
    Used by the health-summary endpoint.
    """
    pipeline = [
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id":         "$node_id",
            "rssi":        {"$first": "$rssi"},
            "latency_ms":  {"$first": "$latency_ms"},
            "packet_loss": {"$first": "$packet_loss"},
            "timestamp":   {"$first": "$timestamp"},
        }},
        {"$project": {
            "node_id":     "$_id",
            "rssi":        1,
            "latency_ms":  1,
            "packet_loss": 1,
            "timestamp":   1,
            "_id":         0,
        }},
    ]
    return list(collection.aggregate(pipeline))


# ── Sensor data CRUD ───────────────────────────────────────────────────────────
def insert_sensor_data(collection: Collection, data: dict) -> str:
    """Insert a sensor-data reading.  Returns inserted _id as string."""
    doc = {
        "timestamp":   utcnow(),
        "node_id":     data["node_id"],
        "temperature": float(data["temperature"]),
        "humidity":    float(data["humidity"]),
    }
    result = collection.insert_one(doc)
    return str(result.inserted_id)
