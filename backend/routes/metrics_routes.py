"""
routes/metrics_routes.py — Metrics & Sensor Data API
-----------------------------------------------------
Endpoints:
  POST  /api/metrics                  Ingest network metrics from gateway
  POST  /api/sensor-data              Ingest environmental sensor readings
  GET   /api/metrics/history          Paginated metrics history
  GET   /api/metrics/analytics        Analytics summary (trends, dead-zones)

Example POST /api/metrics payload:
{
    "node_id":     "NODE-001",
    "rssi":        -65,
    "latency_ms":  12,
    "packet_loss": 2.5,
    "throughput":  48.3
}

Example POST /api/sensor-data payload:
{
    "node_id":     "NODE-001",
    "temperature": 28.4,
    "humidity":    62.1
}
"""

from flask import Blueprint, request, jsonify

from database.db import get_db
from models.metrics_model import (
    insert_metrics, validate_metrics,
    insert_sensor_data, validate_sensor_data,
    get_metrics_history,
)
from models.node_model import update_node_heartbeat
from services.alert_service import evaluate_metrics_alerts
from services.mesh_service import check_offline_nodes
from services.analytics_service import (
    get_rssi_trend, get_packet_loss_trend,
    detect_dead_zones, get_worst_nodes,
)
from utils.logger import get_logger

logger      = get_logger(__name__)
metrics_bp  = Blueprint("metrics", __name__)


# ── POST /api/metrics ─────────────────────────────────────────────────────────
@metrics_bp.route("/metrics", methods=["POST"])
def ingest_metrics():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    valid, error = validate_metrics(data)
    if not valid:
        return jsonify({"error": error}), 422

    db = get_db()

    # Persist the metrics document
    doc_id = insert_metrics(db.metrics, data)

    # Update the node's last_seen timestamp
    update_node_heartbeat(
        db.nodes,
        data["node_id"],
        {"status": "online"},
    )

    # Run alert evaluation (synchronous, fast)
    alert_ids = evaluate_metrics_alerts(
        node_id=data["node_id"],
        rssi=int(data["rssi"]),
        packet_loss=float(data.get("packet_loss", 0.0)),
    )

    # Opportunistically sweep for offline nodes on every ingestion call
    check_offline_nodes()

    return jsonify({
        "message":   "Metrics recorded",
        "doc_id":    doc_id,
        "alerts":    len(alert_ids),
        "alert_ids": alert_ids,
    }), 201


# ── POST /api/sensor-data ─────────────────────────────────────────────────────
@metrics_bp.route("/sensor-data", methods=["POST"])
def ingest_sensor_data():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    valid, error = validate_sensor_data(data)
    if not valid:
        return jsonify({"error": error}), 422

    db     = get_db()
    doc_id = insert_sensor_data(db.sensor_data, data)
    update_node_heartbeat(db.nodes, data["node_id"])

    return jsonify({"message": "Sensor data recorded", "doc_id": doc_id}), 201


# ── GET /api/metrics/history ──────────────────────────────────────────────────
@metrics_bp.route("/metrics/history", methods=["GET"])
def metrics_history():
    node_id  = request.args.get("node_id")
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(200, int(request.args.get("per_page", 50)))

    db      = get_db()
    result  = get_metrics_history(db.metrics, node_id, page, per_page)
    return jsonify(result), 200


# ── GET /api/metrics/analytics ────────────────────────────────────────────────
@metrics_bp.route("/metrics/analytics", methods=["GET"])
def metrics_analytics():
    """
    Returns a rich analytics payload for the dashboard:
    - RSSI trend for a node
    - Packet-loss trend for a node
    - Dead-zone nodes
    - Worst-performing nodes
    """
    node_id = request.args.get("node_id")
    limit   = min(200, int(request.args.get("limit", 50)))

    response: dict = {
        "dead_zones":  detect_dead_zones(),
        "worst_nodes": get_worst_nodes(top_n=5),
    }

    if node_id:
        response["rssi_trend"]        = get_rssi_trend(node_id, limit)
        response["packet_loss_trend"] = get_packet_loss_trend(node_id, limit)

    return jsonify(response), 200
