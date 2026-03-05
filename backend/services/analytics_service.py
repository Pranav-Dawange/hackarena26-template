"""
services/analytics_service.py — Network Analytics & Intelligence
------------------------------------------------------------------
Provides aggregated analytics used by the dashboard:
  - per-node signal trend
  - dead-zone detection
  - worst-performing nodes ranking
  - packet-loss distribution
"""

from database.db import get_db
from utils.logger import get_logger

logger = get_logger(__name__)


def get_rssi_trend(node_id: str, limit: int = 50) -> list:
    """
    Return the last `limit` RSSI readings for a node,
    ordered oldest → newest (suitable for time-series charts).
    """
    db = get_db()
    cursor = (
        db.metrics.find({"node_id": node_id}, {"_id": 0, "timestamp": 1, "rssi": 1})
        .sort("timestamp", -1)
        .limit(limit)
    )
    docs = list(cursor)
    docs.reverse()  # chronological order
    return [{"timestamp": d["timestamp"].isoformat(), "rssi": d["rssi"]} for d in docs]


def get_packet_loss_trend(node_id: str, limit: int = 50) -> list:
    """Return packet-loss trend for a node (oldest → newest)."""
    db = get_db()
    cursor = (
        db.metrics.find(
            {"node_id": node_id},
            {"_id": 0, "timestamp": 1, "packet_loss": 1},
        )
        .sort("timestamp", -1)
        .limit(limit)
    )
    docs = list(cursor)
    docs.reverse()
    return [
        {"timestamp": d["timestamp"].isoformat(), "packet_loss": d["packet_loss"]}
        for d in docs
    ]


def detect_dead_zones(rssi_threshold: int = -85, min_samples: int = 5) -> list:
    """
    Identify nodes that consistently report RSSI below `rssi_threshold`
    over their last `min_samples` readings — indicative of a dead zone.

    Returns a list of dicts: [{"node_id": ..., "avg_rssi": ..., "location": ...}]
    """
    db = get_db()
    pipeline = [
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id":      "$node_id",
            "readings": {"$push": "$rssi"},
            "count":    {"$sum": 1},
        }},
        {"$project": {
            "node_id": "$_id",
            "last_n":  {"$slice": ["$readings", min_samples]},
            "count":   1,
            "_id":     0,
        }},
        {"$match": {"count": {"$gte": min_samples}}},
    ]
    results = list(db.metrics.aggregate(pipeline))

    dead_zones = []
    for r in results:
        avg_rssi = sum(r["last_n"]) / len(r["last_n"])
        if avg_rssi <= rssi_threshold:
            node_doc = db.nodes.find_one({"node_id": r["node_id"]}, {"location": 1})
            dead_zones.append({
                "node_id":  r["node_id"],
                "avg_rssi": round(avg_rssi, 2),
                "location": node_doc.get("location", "unknown") if node_doc else "unknown",
            })

    logger.info("Dead-zone detection found %d nodes below %d dBm", len(dead_zones), rssi_threshold)
    return dead_zones


def get_worst_nodes(top_n: int = 5) -> list:
    """
    Return the `top_n` nodes with the highest average packet loss.
    Useful for prioritising maintenance efforts.
    """
    db = get_db()
    pipeline = [
        {"$group": {
            "_id":              "$node_id",
            "avg_packet_loss":  {"$avg": "$packet_loss"},
            "avg_rssi":         {"$avg": "$rssi"},
            "sample_count":     {"$sum": 1},
        }},
        {"$sort": {"avg_packet_loss": -1}},
        {"$limit": top_n},
        {"$project": {
            "node_id":         "$_id",
            "avg_packet_loss": {"$round": ["$avg_packet_loss", 2]},
            "avg_rssi":        {"$round": ["$avg_rssi", 2]},
            "sample_count":    1,
            "_id":             0,
        }},
    ]
    return list(db.metrics.aggregate(pipeline))
