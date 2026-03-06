"""
mock_data.py — SignalSevak Mock Data Generator
------------------------------------------------
Provides realistic fake data for the Streamlit dashboard so the UI
can be explored without a running backend or database.
"""

import random
from typing import Optional
import pandas as pd
from datetime import datetime, timedelta

# ── Reproducible randomness ────────────────────────────────────────────────────
random.seed(42)

# ── Constants ──────────────────────────────────────────────────────────────────
NOW = datetime(2026, 3, 6, 7, 0, 0)  # fixed "now" for reproducibility

NODE_DEFINITIONS = [
    {"node_id": "NODE-001", "location": "HQ - Server Room",       "ip_address": "192.168.4.1",  "hop_count": 0, "battery_level": None, "status": "online"},
    {"node_id": "NODE-002", "location": "Building A - Floor 1",   "ip_address": "192.168.4.2",  "hop_count": 1, "battery_level": 87,   "status": "online"},
    {"node_id": "NODE-003", "location": "Building A - Floor 2",   "ip_address": "192.168.4.3",  "hop_count": 1, "battery_level": 73,   "status": "online"},
    {"node_id": "NODE-004", "location": "Building B - Entrance",  "ip_address": "192.168.4.4",  "hop_count": 2, "battery_level": 45,   "status": "degraded"},
    {"node_id": "NODE-005", "location": "Building B - Rooftop",   "ip_address": "192.168.4.5",  "hop_count": 2, "battery_level": 12,   "status": "degraded"},
    {"node_id": "NODE-006", "location": "Parking Lot - Zone A",   "ip_address": "192.168.4.6",  "hop_count": 3, "battery_level": 91,   "status": "online"},
    {"node_id": "NODE-007", "location": "Parking Lot - Zone B",   "ip_address": "192.168.4.7",  "hop_count": 3, "battery_level": 60,   "status": "online"},
    {"node_id": "NODE-008", "location": "Warehouse - Section 1",  "ip_address": "192.168.4.8",  "hop_count": 4, "battery_level": 5,    "status": "offline"},
    {"node_id": "NODE-009", "location": "Warehouse - Section 2",  "ip_address": "192.168.4.9",  "hop_count": 4, "battery_level": 33,   "status": "online"},
    {"node_id": "NODE-010", "location": "Guard Post - Main Gate", "ip_address": "192.168.4.10", "hop_count": 5, "battery_level": 78,   "status": "online"},
]

EDGE_DEFINITIONS = [
    ("NODE-001", "NODE-002"),
    ("NODE-001", "NODE-003"),
    ("NODE-002", "NODE-004"),
    ("NODE-003", "NODE-005"),
    ("NODE-004", "NODE-006"),
    ("NODE-004", "NODE-007"),
    ("NODE-006", "NODE-008"),
    ("NODE-007", "NODE-009"),
    ("NODE-009", "NODE-010"),
]

# Node layout positions for topology visualisation (x, y)
NODE_POSITIONS = {
    "NODE-001": (5, 10),
    "NODE-002": (2, 8),
    "NODE-003": (8, 8),
    "NODE-004": (1, 6),
    "NODE-005": (9, 6),
    "NODE-006": (0, 4),
    "NODE-007": (2, 4),
    "NODE-008": (0, 2),
    "NODE-009": (3, 2),
    "NODE-010": (4, 0),
}

# ── Node helpers ───────────────────────────────────────────────────────────────

def get_nodes_df() -> pd.DataFrame:
    """Return a DataFrame of all mesh nodes."""
    rows = []
    for n in NODE_DEFINITIONS:
        last_seen = NOW - timedelta(seconds=random.randint(10, 3600))
        if n["status"] == "offline":
            last_seen = NOW - timedelta(minutes=random.randint(5, 60))
        rows.append({
            "node_id":       n["node_id"],
            "location":      n["location"],
            "status":        n["status"],
            "battery_level": n["battery_level"],
            "ip_address":    n["ip_address"],
            "hop_count":     n["hop_count"],
            "last_seen":     last_seen.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return pd.DataFrame(rows)


def get_topology() -> dict:
    """Return nodes + edges for topology graph."""
    return {
        "nodes": NODE_DEFINITIONS,
        "edges": [{"from": e[0], "to": e[1]} for e in EDGE_DEFINITIONS],
        "positions": NODE_POSITIONS,
    }


# ── Metrics helpers ────────────────────────────────────────────────────────────

def _rssi_for_node(node_id: str) -> float:
    """Base RSSI varies by hop count / node health."""
    base = {
        "NODE-001": -45,
        "NODE-002": -55,
        "NODE-003": -58,
        "NODE-004": -72,
        "NODE-005": -78,
        "NODE-006": -62,
        "NODE-007": -65,
        "NODE-008": -95,
        "NODE-009": -68,
        "NODE-010": -74,
    }
    return base.get(node_id, -70)


def get_metrics_df(node_id: Optional[str] = None, hours: int = 24) -> pd.DataFrame:
    """Return time-series metrics for one or all nodes over last `hours`."""
    rows = []
    nodes = [n for n in NODE_DEFINITIONS if node_id is None or n["node_id"] == node_id]
    for n in nodes:
        base_rssi    = _rssi_for_node(n["node_id"])
        base_latency = 10 + n["hop_count"] * 8
        base_loss    = 1.0 + n["hop_count"] * 1.5
        if n["status"] == "offline":
            base_loss = 60.0
        base_tp = max(5.0, 100.0 - n["hop_count"] * 12.0)

        for i in range(hours * 2):  # every 30 min
            ts = NOW - timedelta(minutes=30 * (hours * 2 - i))
            rows.append({
                "timestamp":   ts,
                "node_id":     n["node_id"],
                "location":    n["location"],
                "rssi":        round(base_rssi    + random.uniform(-8, 4), 1),
                "latency_ms":  round(base_latency + random.uniform(-3, 15), 1),
                "packet_loss": round(max(0, base_loss + random.uniform(-1, 3)), 2),
                "throughput":  round(max(0, base_tp  + random.uniform(-10, 10)), 1),
            })
    return pd.DataFrame(rows).sort_values("timestamp")


def get_metrics_summary_df() -> pd.DataFrame:
    """Return avg metrics per node for ranking tables."""
    df   = get_metrics_df()
    agg  = df.groupby(["node_id", "location"]).agg(
        avg_rssi        = ("rssi",        "mean"),
        avg_latency_ms  = ("latency_ms",  "mean"),
        avg_packet_loss = ("packet_loss", "mean"),
        avg_throughput  = ("throughput",  "mean"),
    ).reset_index()
    agg["avg_rssi"]        = agg["avg_rssi"].round(1)
    agg["avg_latency_ms"]  = agg["avg_latency_ms"].round(1)
    agg["avg_packet_loss"] = agg["avg_packet_loss"].round(2)
    agg["avg_throughput"]  = agg["avg_throughput"].round(1)
    return agg.sort_values("avg_rssi")


# ── Sensor data helpers ────────────────────────────────────────────────────────

def get_sensor_df(node_id: Optional[str] = None, hours: int = 24) -> pd.DataFrame:
    """Return temperature + humidity readings per node."""
    base_temp = {
        "NODE-001": 24, "NODE-002": 26, "NODE-003": 25,
        "NODE-004": 29, "NODE-005": 35, "NODE-006": 22,
        "NODE-007": 23, "NODE-008": 31, "NODE-009": 28,
        "NODE-010": 21,
    }
    base_hum = {
        "NODE-001": 45, "NODE-002": 52, "NODE-003": 50,
        "NODE-004": 60, "NODE-005": 70, "NODE-006": 40,
        "NODE-007": 42, "NODE-008": 65, "NODE-009": 58,
        "NODE-010": 38,
    }
    rows = []
    nodes = [n for n in NODE_DEFINITIONS if node_id is None or n["node_id"] == node_id]
    for n in nodes:
        nid = n["node_id"]
        for i in range(hours * 2):
            ts = NOW - timedelta(minutes=30 * (hours * 2 - i))
            rows.append({
                "timestamp":   ts,
                "node_id":     nid,
                "location":    n["location"],
                "temperature": round(base_temp[nid] + random.uniform(-2, 2), 1),
                "humidity":    round(base_hum[nid]  + random.uniform(-5, 5), 1),
            })
    return pd.DataFrame(rows).sort_values("timestamp")


# ── Alerts / Events helpers ────────────────────────────────────────────────────

def get_events_df() -> pd.DataFrame:
    """Return a realistic mix of system events."""
    templates = [
        ("NODE_OFFLINE",       "critical", "NODE-008", "Node {n} has gone offline. Last seen {ago} minutes ago."),
        ("WEAK_SIGNAL",        "warning",  "NODE-005", "RSSI dropped to -91 dBm on {n}. Check antenna or obstructions."),
        ("WEAK_SIGNAL",        "warning",  "NODE-004", "RSSI reading -82 dBm on {n}. Signal below threshold."),
        ("HIGH_PACKET_LOSS",   "critical", "NODE-008", "Packet loss at 65% on {n}. Route is unstable."),
        ("HIGH_PACKET_LOSS",   "warning",  "NODE-005", "Packet loss at 28% on {n}."),
        ("REROUTE",            "info",     "NODE-004", "Node {n} rerouted: NODE-003 → NODE-002."),
        ("REROUTE",            "info",     "NODE-009", "Node {n} rerouted: NODE-007 → NODE-006."),
        ("NODE_ONLINE",        "info",     "NODE-009", "Node {n} came back online."),
        ("NODE_ONLINE",        "info",     "NODE-010", "Node {n} registered for the first time."),
        ("LOW_BATTERY",        "warning",  "NODE-005", "Battery at 12% on {n}. Replace soon."),
        ("LOW_BATTERY",        "critical", "NODE-008", "Battery at 5% on {n}. Node may go offline."),
        ("LATENCY_SPIKE",      "warning",  "NODE-010", "Latency spike to 142 ms on {n}."),
        ("LATENCY_SPIKE",      "info",     "NODE-006", "Latency briefly elevated to 55 ms on {n}."),
        ("THROUGHPUT_DROP",    "warning",  "NODE-004", "Throughput fell to 8 kbps on {n}. Possible congestion."),
        ("NODE_HEARTBEAT_OK",  "info",     "NODE-001", "Gateway {n} heartbeat nominal."),
        ("NODE_HEARTBEAT_OK",  "info",     "NODE-002", "Node {n} heartbeat OK."),
        ("DEAD_ZONE_DETECTED", "warning",  "NODE-008", "Dead zone detected around {n}. Coverage gap."),
        ("CONFIG_UPDATED",     "info",     "NODE-001", "Gateway {n} configuration refreshed."),
        ("MESH_SCAN",          "info",     "NODE-001", "Full mesh scan completed — 10 nodes discovered."),
        ("ALERT_CLEARED",      "info",     "NODE-004", "RSSI threshold alert cleared for {n}."),
    ]

    rows = []
    resolved_set = {0, 1, 4, 6, 7, 8, 11, 14, 15, 17, 18}  # indices of resolved events
    for idx, (etype, severity, nid, msg_tpl) in enumerate(templates):
        ago = random.randint(2, 120)
        ts  = NOW - timedelta(minutes=ago + idx * 15)
        rows.append({
            "id":         f"EVT-{1000 + idx:04d}",
            "timestamp":  ts.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": etype,
            "node_id":    nid,
            "severity":   severity,
            "message":    msg_tpl.format(n=nid, ago=ago),
            "resolved":   idx in resolved_set,
        })

    return pd.DataFrame(rows).sort_values("timestamp", ascending=False)


# ── Summary KPIs ───────────────────────────────────────────────────────────────

def get_kpi_summary() -> dict:
    nodes_df   = get_nodes_df()
    metrics_df = get_metrics_df()
    events_df  = get_events_df()

    total   = len(nodes_df)
    online  = (nodes_df["status"] == "online").sum()
    offline = (nodes_df["status"] == "offline").sum()
    degrad  = (nodes_df["status"] == "degraded").sum()

    avg_rssi       = metrics_df["rssi"].mean()
    avg_latency    = metrics_df["latency_ms"].mean()
    avg_pkt_loss   = metrics_df["packet_loss"].mean()
    active_alerts  = (~events_df["resolved"]).sum()
    critical_alerts= ((events_df["severity"] == "critical") & (~events_df["resolved"])).sum()

    # Nodes with RSSI < -80 → dead zone candidates
    last_rssi = (
        metrics_df.sort_values("timestamp")
        .groupby("node_id")["rssi"]
        .last()
    )
    dead_zones = (last_rssi < -80).sum()

    return {
        "total_nodes":     total,
        "online_nodes":    int(online),
        "offline_nodes":   int(offline),
        "degraded_nodes":  int(degrad),
        "online_pct":      round(online / total * 100, 1),
        "avg_rssi":        round(avg_rssi, 1),
        "avg_latency_ms":  round(avg_latency, 1),
        "avg_packet_loss": round(avg_pkt_loss, 2),
        "active_alerts":   int(active_alerts),
        "critical_alerts": int(critical_alerts),
        "dead_zones":      int(dead_zones),
    }
