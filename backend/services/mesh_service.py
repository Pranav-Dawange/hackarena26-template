"""
services/mesh_service.py — Mesh Network Business Logic
-------------------------------------------------------
Higher-level operations that coordinate between multiple models:
  - Registering / updating nodes
  - Building the network topology graph
  - Detecting offline nodes
  - Generating system health summaries
"""

from datetime import datetime, timezone, timedelta
from database.db import get_db
from models.node_model import (
    create_node, get_all_nodes, get_node_by_id,
    update_node_heartbeat, set_node_status, validate_node,
)
from models.metrics_model import get_latest_metrics_per_node
from models.event_model import log_event
from utils.logger import get_logger
from flask import current_app

logger = get_logger(__name__)


def register_or_update_node(data: dict) -> tuple[dict, bool]:
    """
    Register a new node or refresh an existing one.

    Returns
    -------
    (node_doc, created)  — created is True if new, False if updated.
    """
    db = get_db()
    valid, error = validate_node(data)
    if not valid:
        raise ValueError(error)

    existing = get_node_by_id(db.nodes, data["node_id"])
    if existing:
        extras = {k: data[k] for k in ("status", "battery_level", "ip_address", "hop_count") if k in data}
        update_node_heartbeat(db.nodes, data["node_id"], extras)
        logger.debug("Heartbeat updated for node %s", data["node_id"])
        return get_node_by_id(db.nodes, data["node_id"]), False
    else:
        node = create_node(db.nodes, data)
        log_event(
            db.events,
            "NODE_ONLINE",
            f"Node {data['node_id']} registered for the first time.",
            node_id=data["node_id"],
            severity="info",
        )
        logger.info("New node registered: %s", data["node_id"])
        return node, True


def get_network_topology() -> dict:
    """
    Build a simple topology representation.

    Returns a graph structure:
    {
        "nodes": [...],
        "edges": [{"source": ..., "target": ..., "rssi": ...}]
    }
    Note: true multi-hop edge data would come from the firmware; here
    we infer edges from shared hop_count levels as a simplified model.
    """
    db     = get_db()
    nodes  = get_all_nodes(db.nodes)
    latest = {m["node_id"]: m for m in get_latest_metrics_per_node(db.metrics)}

    # Enrich node list with latest metrics
    enriched_nodes = []
    for node in nodes:
        nid = node["node_id"]
        m   = latest.get(nid, {})
        enriched_nodes.append({
            **node,
            "rssi":        m.get("rssi"),
            "latency_ms":  m.get("latency_ms"),
            "packet_loss": m.get("packet_loss"),
        })

    # Minimal edge heuristic: nodes with hop_count N connect to a node at N-1
    hop_groups: dict[int, list] = {}
    for node in enriched_nodes:
        hop = node.get("hop_count", 0)
        hop_groups.setdefault(hop, []).append(node["node_id"])

    edges = []
    sorted_hops = sorted(hop_groups.keys())
    for i, hop in enumerate(sorted_hops[1:], start=1):
        parent_hop   = sorted_hops[i - 1]
        parent_nodes = hop_groups[parent_hop]
        for child_id in hop_groups[hop]:
            parent_id = parent_nodes[0]  # simplified: attach to first at parent level
            child_metrics = latest.get(child_id, {})
            edges.append({
                "source": parent_id,
                "target": child_id,
                "rssi":   child_metrics.get("rssi"),
            })

    return {"nodes": enriched_nodes, "edges": edges}


def get_network_health() -> dict:
    """
    Return an aggregate health summary across the entire mesh.
    """
    db      = get_db()
    nodes   = get_all_nodes(db.nodes)
    latest  = get_latest_metrics_per_node(db.metrics)
    metrics_by_node = {m["node_id"]: m for m in latest}

    total   = len(nodes)
    online  = sum(1 for n in nodes if n["status"] == "online")
    offline = sum(1 for n in nodes if n["status"] == "offline")
    degraded= sum(1 for n in nodes if n["status"] == "degraded")

    avg_rssi         = None
    avg_packet_loss  = None
    if latest:
        avg_rssi        = round(sum(m["rssi"] for m in latest) / len(latest), 2)
        avg_packet_loss = round(
            sum(m["packet_loss"] for m in latest) / len(latest), 2
        )

    return {
        "total_nodes":      total,
        "online":           online,
        "offline":          offline,
        "degraded":         degraded,
        "healthy_percent":  round(online / total * 100, 1) if total else 0,
        "avg_rssi_dbm":     avg_rssi,
        "avg_packet_loss":  avg_packet_loss,
    }


def check_offline_nodes() -> list[str]:
    """
    Compare last_seen timestamps against NODE_OFFLINE_TIMEOUT.
    Mark stale nodes as offline and log events.

    Call periodically from a scheduler or on every metrics ingestion.
    Returns list of node_ids that were just marked offline.
    """
    db      = get_db()
    timeout = current_app.config["NODE_OFFLINE_TIMEOUT"]
    cutoff  = datetime.now(timezone.utc) - timedelta(seconds=timeout)

    stale   = list(db.nodes.find({"status": "online", "last_seen": {"$lt": cutoff}}))
    newly_offline = []

    for node in stale:
        nid = node["node_id"]
        set_node_status(db.nodes, nid, "offline")
        log_event(
            db.events, "NODE_OFFLINE",
            f"Node {nid} has not sent a heartbeat for >{timeout}s.",
            node_id=nid, severity="critical",
        )
        logger.warning("Node %s marked OFFLINE (last_seen: %s)", nid, node["last_seen"])
        newly_offline.append(nid)

    return newly_offline
