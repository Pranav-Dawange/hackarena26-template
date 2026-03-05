"""
services/alert_service.py — Threshold-Based Alert Engine
---------------------------------------------------------
Evaluates incoming metrics against configured thresholds and logs
events when violations are detected.

Designed to run synchronously inside the metrics ingestion endpoint —
lightweight enough to complete within a single HTTP request cycle.
"""

from flask import current_app
from database.db import get_db
from models.event_model import log_event
from utils.logger import get_logger

logger = get_logger(__name__)


def evaluate_metrics_alerts(node_id: str, rssi: int, packet_loss: float) -> list[str]:
    """
    Check a freshly ingested metrics payload against alert thresholds.

    Parameters
    ----------
    node_id      : the reporting mesh node
    rssi         : signal strength in dBm
    packet_loss  : percentage (0–100)

    Returns
    -------
    List of alert event_ids that were created (empty if no alerts fired).
    """
    db              = get_db()
    rssi_threshold  = current_app.config["RSSI_ALERT_THRESHOLD"]
    loss_threshold  = current_app.config["PACKET_LOSS_THRESHOLD"]
    alert_ids: list = []

    # ── Weak-signal check ─────────────────────────────────────────────────
    if rssi < rssi_threshold:
        msg = (
            f"Node {node_id} RSSI {rssi} dBm is below threshold "
            f"{rssi_threshold} dBm. Possible dead-zone or obstruction."
        )
        eid = log_event(db.events, "WEAK_SIGNAL", msg, node_id=node_id, severity="warning")
        logger.warning("WEAK_SIGNAL alert for %s: %d dBm", node_id, rssi)
        alert_ids.append(eid)

    # ── High packet-loss check ────────────────────────────────────────────
    if packet_loss > loss_threshold:
        msg = (
            f"Node {node_id} packet loss {packet_loss:.1f}% exceeds "
            f"threshold {loss_threshold:.1f}%."
        )
        eid = log_event(
            db.events, "HIGH_PACKET_LOSS", msg, node_id=node_id, severity="warning"
        )
        logger.warning("HIGH_PACKET_LOSS alert for %s: %.1f%%", node_id, packet_loss)
        alert_ids.append(eid)

    return alert_ids


def fire_node_offline_alert(node_id: str) -> str:
    """Manually fire a NODE_OFFLINE alert (called by mesh_service)."""
    db  = get_db()
    msg = f"Node {node_id} is unreachable. Topology may have rerouted."
    eid = log_event(db.events, "NODE_OFFLINE", msg, node_id=node_id, severity="critical")
    logger.error("NODE_OFFLINE alert fired for %s", node_id)
    return eid


def fire_reroute_event(node_id: str, old_parent: str, new_parent: str) -> str:
    """Log a reroute event when the mesh topology changes."""
    db  = get_db()
    msg = f"Node {node_id} rerouted from parent {old_parent} → {new_parent}."
    eid = log_event(db.events, "REROUTE", msg, node_id=node_id, severity="info")
    logger.info("REROUTE event logged for %s", node_id)
    return eid
