"""
routes/node_routes.py — Node Management API
--------------------------------------------
Endpoints:
  POST  /api/node/register              Register or heartbeat a node
  GET   /api/nodes                      List all nodes
  GET   /api/nodes/<node_id>            Get a single node
  GET   /api/network/topology           Network graph (nodes + edges)
  GET   /api/network/health             Aggregate health summary
  POST  /api/network/check-offline      Trigger offline detection sweep

Example payload for POST /api/node/register:
{
    "node_id":       "NODE-001",
    "location":      "Building A - Floor 2",
    "battery_level": 87,
    "ip_address":    "192.168.4.2",
    "hop_count":     1
}
"""

from flask import Blueprint, request, jsonify
from pymongo.errors import DuplicateKeyError

from services.mesh_service import (
    register_or_update_node,
    get_network_topology,
    get_network_health,
    check_offline_nodes,
)
from models.node_model import get_all_nodes, get_node_by_id
from database.db import get_db
from utils.logger import get_logger

logger  = get_logger(__name__)
node_bp = Blueprint("node", __name__)


# ── POST /api/node/register ───────────────────────────────────────────────────
@node_bp.route("/node/register", methods=["POST"])
def register_node():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    try:
        node, created = register_or_update_node(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except DuplicateKeyError:
        return jsonify({"error": "node_id conflict during concurrent insert"}), 409

    status_code = 201 if created else 200
    return jsonify({
        "message": "Node registered" if created else "Node heartbeat updated",
        "node":    node,
    }), status_code


# ── GET /api/nodes ────────────────────────────────────────────────────────────
@node_bp.route("/nodes", methods=["GET"])
def list_nodes():
    db    = get_db()
    nodes = get_all_nodes(db.nodes)
    return jsonify({"count": len(nodes), "nodes": nodes}), 200


# ── GET /api/nodes/<node_id> ──────────────────────────────────────────────────
@node_bp.route("/nodes/<string:node_id>", methods=["GET"])
def get_node(node_id: str):
    db   = get_db()
    node = get_node_by_id(db.nodes, node_id)
    if not node:
        return jsonify({"error": f"Node '{node_id}' not found"}), 404
    return jsonify(node), 200


# ── GET /api/network/topology ─────────────────────────────────────────────────
@node_bp.route("/network/topology", methods=["GET"])
def network_topology():
    topology = get_network_topology()
    return jsonify(topology), 200


# ── GET /api/network/health ───────────────────────────────────────────────────
@node_bp.route("/network/health", methods=["GET"])
def network_health():
    health = get_network_health()
    return jsonify(health), 200


# ── POST /api/network/check-offline ──────────────────────────────────────────
@node_bp.route("/network/check-offline", methods=["POST"])
def trigger_offline_check():
    """
    Manually trigger an offline-node sweep.
    In production this would be called by a scheduler (e.g. APScheduler / cron).
    """
    offline = check_offline_nodes()
    return jsonify({
        "message":          f"{len(offline)} node(s) marked offline",
        "offline_node_ids": offline,
    }), 200
