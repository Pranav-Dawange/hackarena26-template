"""
routes/alert_routes.py — Events & Alerts API
---------------------------------------------
Endpoints:
  GET   /api/events                   Paginated event log
  POST  /api/events/<id>/resolve      Mark an event as resolved
  POST  /api/events/reroute           Log a manual reroute event

Example GET /api/events response:
{
  "data": [
    {
      "id": "...",
      "timestamp": "...",
      "event_type": "NODE_OFFLINE",
      "node_id": "NODE-002",
      "severity": "critical",
      "message": "...",
      "resolved": false
    }
  ],
  "page": 1,
  "per_page": 50,
  "total": 12
}
"""

from flask import Blueprint, request, jsonify

from database.db import get_db
from models.event_model import get_recent_events, resolve_event, log_event
from services.alert_service import fire_reroute_event
from utils.logger import get_logger

logger   = get_logger(__name__)
alert_bp = Blueprint("alerts", __name__)


# ── GET /api/events ───────────────────────────────────────────────────────────
@alert_bp.route("/events", methods=["GET"])
def list_events():
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(200, int(request.args.get("per_page", 50)))
    node_id  = request.args.get("node_id")
    severity = request.args.get("severity")  # info | warning | critical

    db     = get_db()
    result = get_recent_events(db.events, page, per_page, node_id, severity)
    return jsonify(result), 200


# ── POST /api/events/<id>/resolve ─────────────────────────────────────────────
@alert_bp.route("/events/<string:event_id>/resolve", methods=["POST"])
def resolve_alert(event_id: str):
    db      = get_db()
    success = resolve_event(db.events, event_id)
    if not success:
        return jsonify({"error": f"Event '{event_id}' not found"}), 404
    return jsonify({"message": "Event marked as resolved"}), 200


# ── POST /api/events/reroute ──────────────────────────────────────────────────
@alert_bp.route("/events/reroute", methods=["POST"])
def log_reroute():
    """
    Called by the gateway ESP32 when it detects a topology change.

    Expected payload:
    {
        "node_id":    "NODE-003",
        "old_parent": "NODE-002",
        "new_parent": "NODE-001"
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    required = {"node_id", "old_parent", "new_parent"}
    missing  = required - data.keys()
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 422

    eid = fire_reroute_event(data["node_id"], data["old_parent"], data["new_parent"])
    return jsonify({"message": "Reroute event logged", "event_id": eid}), 201


# ── POST /api/events (manual) ─────────────────────────────────────────────────
@alert_bp.route("/events", methods=["POST"])
def create_event():
    """
    Manually log a custom system event from the dashboard or external tooling.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    required = {"event_type", "message"}
    missing  = required - data.keys()
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 422

    db  = get_db()
    eid = log_event(
        db.events,
        event_type=data["event_type"],
        message=data["message"],
        node_id=data.get("node_id"),
        severity=data.get("severity", "info"),
    )
    return jsonify({"message": "Event logged", "event_id": eid}), 201
