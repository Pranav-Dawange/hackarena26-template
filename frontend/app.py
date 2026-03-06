"""
app.py — SignalSevak Streamlit Dashboard
-----------------------------------------
A fully self-contained dashboard that works with mock data.
Run with:   streamlit run frontend/app.py
"""

import sys
import os

# Make sure mock_data is importable regardless of working directory
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from mock_data import (
    get_nodes_df,
    get_topology,
    get_metrics_df,
    get_metrics_summary_df,
    get_sensor_df,
    get_events_df,
    get_kpi_summary,
    NODE_DEFINITIONS,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SignalSevak — Mesh Network Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark sidebar header */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

/* KPI cards */
.kpi-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    transition: transform 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-label {
    font-size: 12px;
    font-weight: 500;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.kpi-value {
    font-size: 36px;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1.2;
    margin: 4px 0;
}
.kpi-sub {
    font-size: 12px;
    color: #64748b;
}
.kpi-good  { color: #22c55e !important; }
.kpi-warn  { color: #f59e0b !important; }
.kpi-crit  { color: #ef4444 !important; }
.kpi-info  { color: #38bdf8 !important; }

/* Status badges */
.badge-online   { background:#166534; color:#bbf7d0; border-radius:6px; padding:2px 10px; font-size:12px; font-weight:600; }
.badge-offline  { background:#7f1d1d; color:#fecaca; border-radius:6px; padding:2px 10px; font-size:12px; font-weight:600; }
.badge-degraded { background:#78350f; color:#fde68a; border-radius:6px; padding:2px 10px; font-size:12px; font-weight:600; }
.badge-critical { background:#7f1d1d; color:#fecaca; border-radius:6px; padding:2px 10px; font-size:11px; font-weight:600; }
.badge-warning  { background:#78350f; color:#fde68a; border-radius:6px; padding:2px 10px; font-size:11px; font-weight:600; }
.badge-info     { background:#0c4a6e; color:#bae6fd; border-radius:6px; padding:2px 10px; font-size:11px; font-weight:600; }

/* Section header */
.section-header {
    font-size: 18px;
    font-weight: 600;
    color: #e2e8f0;
    border-left: 4px solid #38bdf8;
    padding-left: 12px;
    margin: 24px 0 12px 0;
}

/* Divider */
hr { border-color: #1e293b; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 SignalSevak")
    st.markdown("*Mesh Network Monitoring*")
    st.divider()

    page = st.radio(
        "Navigate",
        options=[
            "🌐 Network Overview",
            "📡 Metrics & Analytics",
            "🌡️ Sensor Data",
            "🚨 Alerts & Events",
            "🔍 Node Detail",
        ],
        label_visibility="collapsed",
    )
    st.divider()

    kpi = get_kpi_summary()
    st.markdown(f"**Total Nodes:** {kpi['total_nodes']}")
    st.markdown(f"**🟢 Online:** {kpi['online_nodes']}")
    st.markdown(f"**🟡 Degraded:** {kpi['degraded_nodes']}")
    st.markdown(f"**🔴 Offline:** {kpi['offline_nodes']}")
    st.divider()
    st.caption("Powered by SignalSevak v1.0")
    st.caption("📅 Mock data snapshot: 2026-03-06")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — NETWORK OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "🌐 Network Overview":
    st.title("🌐 Network Overview")
    st.markdown("Real-time health summary of the entire SignalSevak mesh network.")
    st.divider()

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    kpi = get_kpi_summary()
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    def kpi_card(col, label, value, sub="", cls="kpi-info"):
        col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value {cls}">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi_card(c1, "Total Nodes",   kpi["total_nodes"],    "in mesh",              "kpi-info")
    kpi_card(c2, "Online",        f"{kpi['online_pct']}%", f"{kpi['online_nodes']} nodes", "kpi-good")
    kpi_card(c3, "Avg RSSI",      f"{kpi['avg_rssi']} dBm", "signal strength",     "kpi-warn")
    kpi_card(c4, "Avg Latency",   f"{kpi['avg_latency_ms']} ms", "round-trip",      "kpi-info")
    kpi_card(c5, "Active Alerts", kpi["active_alerts"],   f"{kpi['critical_alerts']} critical", "kpi-crit" if kpi["critical_alerts"] > 0 else "kpi-warn")
    kpi_card(c6, "Dead Zones",    kpi["dead_zones"],      "RSSI < -80 dBm",       "kpi-warn")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Topology Graph ────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Network Topology</div>', unsafe_allow_html=True)

    topo = get_topology()
    pos  = topo["positions"]

    STATUS_COLOUR = {"online": "#22c55e", "degraded": "#f59e0b", "offline": "#ef4444"}

    edge_x, edge_y = [], []
    for edge in topo["edges"]:
        x0, y0 = pos[edge["from"]]
        x1, y1 = pos[edge["to"]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
    for n in topo["nodes"]:
        nid = n["node_id"]
        x, y = pos[nid]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"<b>{nid}</b><br>{n['location']}<br>Status: {n['status']}<br>Hops: {n['hop_count']}")
        node_color.append(STATUS_COLOUR.get(n["status"], "#64748b"))
        node_size.append(24 if n["hop_count"] == 0 else 18)

    fig_topo = go.Figure()
    fig_topo.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=2, color="#334155"),
        hoverinfo="none",
        name="Links",
    ))
    fig_topo.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(size=node_size, color=node_color, line=dict(width=2, color="#0f172a")),
        text=[n["node_id"] for n in topo["nodes"]],
        textposition="top center",
        textfont=dict(color="#e2e8f0", size=11),
        hovertext=node_text,
        hoverinfo="text",
        name="Nodes",
    ))
    fig_topo.update_layout(
        height=420,
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"),
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=20, r=20, t=20, b=20),
        hoverlabel=dict(bgcolor="#1e293b", font_color="#e2e8f0"),
    )
    st.plotly_chart(fig_topo, use_container_width=True)

    # ── Node Status Table ─────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Node Status Table</div>', unsafe_allow_html=True)
    nodes_df = get_nodes_df()

    def badge(status):
        return f'<span class="badge-{status}">{status.upper()}</span>'

    display = nodes_df.copy()
    display["status"] = display["status"].apply(badge)
    display["battery_level"] = display["battery_level"].apply(
        lambda x: f"{int(x)}%" if x is not None else "⚡ Wired"
    )
    display.columns = ["Node ID", "Location", "Status", "Battery", "IP Address", "Hops", "Last Seen"]

    st.markdown(display.to_html(escape=False, index=False), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — METRICS & ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📡 Metrics & Analytics":
    st.title("📡 Metrics & Analytics")
    st.markdown("Network performance metrics — RSSI, latency, packet loss, and throughput.")
    st.divider()

    col_sel, col_hr = st.columns([3, 1])
    with col_sel:
        node_ids   = [n["node_id"] for n in NODE_DEFINITIONS]
        sel_node   = st.selectbox("Select Node", node_ids, index=0)
    with col_hr:
        hours = st.selectbox("Time Range", [6, 12, 24], index=2, format_func=lambda h: f"Last {h}h")

    df = get_metrics_df(sel_node, hours)

    # Metric KPIs
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg RSSI",        f"{df['rssi'].mean():.1f} dBm",        delta=f"{df['rssi'].iloc[-1] - df['rssi'].mean():.1f}")
    m2.metric("Avg Latency",     f"{df['latency_ms'].mean():.1f} ms",    delta=f"{df['latency_ms'].iloc[-1] - df['latency_ms'].mean():.1f} ms")
    m3.metric("Avg Packet Loss", f"{df['packet_loss'].mean():.2f}%",     delta=f"{df['packet_loss'].iloc[-1] - df['packet_loss'].mean():.2f}%")
    m4.metric("Avg Throughput",  f"{df['throughput'].mean():.1f} kbps",  delta=f"{df['throughput'].iloc[-1] - df['throughput'].mean():.1f}")

    # Charts
    chart_cfg = dict(template="plotly_dark", height=280, margin=dict(l=40, r=20, t=40, b=40))

    st.markdown('<div class="section-header">RSSI Trend (dBm)</div>', unsafe_allow_html=True)
    fig_rssi = px.line(df, x="timestamp", y="rssi", color_discrete_sequence=["#38bdf8"],
                       labels={"rssi": "RSSI (dBm)", "timestamp": ""})
    fig_rssi.add_hline(y=-80, line_dash="dash", line_color="#ef4444",
                       annotation_text="Alert Threshold (-80 dBm)", annotation_position="bottom right")
    fig_rssi.update_layout(**chart_cfg, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")
    st.plotly_chart(fig_rssi, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-header">Latency (ms)</div>', unsafe_allow_html=True)
        fig_lat = px.line(df, x="timestamp", y="latency_ms", color_discrete_sequence=["#a78bfa"],
                          labels={"latency_ms": "Latency (ms)", "timestamp": ""})
        fig_lat.update_layout(**chart_cfg, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")
        st.plotly_chart(fig_lat, use_container_width=True)

    with c2:
        st.markdown('<div class="section-header">Packet Loss (%)</div>', unsafe_allow_html=True)
        fig_pl = px.area(df, x="timestamp", y="packet_loss", color_discrete_sequence=["#f97316"],
                         labels={"packet_loss": "Packet Loss (%)", "timestamp": ""})
        fig_pl.add_hline(y=20, line_dash="dash", line_color="#ef4444", annotation_text="Threshold 20%")
        fig_pl.update_layout(**chart_cfg, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")
        st.plotly_chart(fig_pl, use_container_width=True)

    st.markdown('<div class="section-header">Throughput (kbps)</div>', unsafe_allow_html=True)
    fig_tp = px.bar(df.iloc[::4], x="timestamp", y="throughput",
                    color_discrete_sequence=["#22c55e"],
                    labels={"throughput": "Throughput (kbps)", "timestamp": ""})
    fig_tp.update_layout(**chart_cfg, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")
    st.plotly_chart(fig_tp, use_container_width=True)

    # Worst nodes ranking
    st.markdown('<div class="section-header">⚠️ Worst Performing Nodes</div>', unsafe_allow_html=True)
    summary = get_metrics_summary_df().head(5)
    summary.columns = ["Node ID", "Location", "Avg RSSI (dBm)", "Avg Latency (ms)", "Avg Pkt Loss (%)", "Avg Throughput (kbps)"]
    st.dataframe(summary, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — SENSOR DATA
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌡️ Sensor Data":
    st.title("🌡️ Sensor Data")
    st.markdown("Environmental readings from each mesh node — temperature and humidity.")
    st.divider()

    col_sel, col_hr = st.columns([3, 1])
    with col_sel:
        node_ids  = [n["node_id"] for n in NODE_DEFINITIONS]
        sel_node  = st.selectbox("Select Node", node_ids, index=0)
    with col_hr:
        hours = st.selectbox("Time Range", [6, 12, 24], index=2, format_func=lambda h: f"Last {h}h")

    df = get_sensor_df(sel_node, hours)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Current Temp",   f"{df['temperature'].iloc[-1]:.1f} °C")
    s2.metric("Avg Temp",       f"{df['temperature'].mean():.1f} °C",
              delta=f"{df['temperature'].iloc[-1] - df['temperature'].mean():.1f}")
    s3.metric("Current Humidity", f"{df['humidity'].iloc[-1]:.1f} %")
    s4.metric("Avg Humidity",     f"{df['humidity'].mean():.1f} %",
              delta=f"{df['humidity'].iloc[-1] - df['humidity'].mean():.1f}")

    chart_cfg = dict(template="plotly_dark", height=300, margin=dict(l=40, r=20, t=40, b=40))

    st.markdown('<div class="section-header">Temperature Trend (°C)</div>', unsafe_allow_html=True)
    fig_temp = px.line(df, x="timestamp", y="temperature",
                       color_discrete_sequence=["#f97316"],
                       labels={"temperature": "Temperature (°C)", "timestamp": ""})
    fig_temp.update_layout(**chart_cfg, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")
    st.plotly_chart(fig_temp, use_container_width=True)

    st.markdown('<div class="section-header">Humidity Trend (%)</div>', unsafe_allow_html=True)
    fig_hum = px.area(df, x="timestamp", y="humidity",
                      color_discrete_sequence=["#38bdf8"],
                      labels={"humidity": "Humidity (%)", "timestamp": ""})
    fig_hum.update_layout(**chart_cfg, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")
    st.plotly_chart(fig_hum, use_container_width=True)

    # Summary across all nodes
    st.markdown('<div class="section-header">All Nodes — Latest Readings</div>', unsafe_allow_html=True)
    all_sensor = get_sensor_df()
    latest = (
        all_sensor.sort_values("timestamp")
        .groupby("node_id")
        .last()
        .reset_index()[["node_id", "location", "temperature", "humidity"]]
    )
    latest.columns = ["Node ID", "Location", "Temp (°C)", "Humidity (%)"]
    st.dataframe(latest, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — ALERTS & EVENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🚨 Alerts & Events":
    st.title("🚨 Alerts & Events")
    st.markdown("System event log with filtering by severity, node, and resolution status.")
    st.divider()

    events_df = get_events_df()

    # Filters
    f1, f2, f3 = st.columns(3)
    with f1:
        sev_filter = st.multiselect(
            "Severity",
            ["critical", "warning", "info"],
            default=["critical", "warning", "info"],
        )
    with f2:
        all_nodes = ["All"] + sorted(events_df["node_id"].unique().tolist())
        node_filter = st.selectbox("Node", all_nodes)
    with f3:
        res_filter = st.selectbox("Resolution", ["All", "Unresolved", "Resolved"])

    # Apply filters
    filtered = events_df[events_df["severity"].isin(sev_filter)]
    if node_filter != "All":
        filtered = filtered[filtered["node_id"] == node_filter]
    if res_filter == "Unresolved":
        filtered = filtered[~filtered["resolved"]]
    elif res_filter == "Resolved":
        filtered = filtered[filtered["resolved"]]

    # Summary KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Showing Events", len(filtered), f"of {len(events_df)} total")
    k2.metric("Critical",  (filtered["severity"] == "critical").sum())
    k3.metric("Unresolved", (~filtered["resolved"]).sum())

    st.markdown(f"<br>", unsafe_allow_html=True)

    # Severity chart
    sev_counts = filtered["severity"].value_counts().reset_index()
    sev_counts.columns = ["severity", "count"]
    colour_map = {"critical": "#ef4444", "warning": "#f59e0b", "info": "#38bdf8"}
    fig_sev = px.bar(sev_counts, x="severity", y="count",
                     color="severity", color_discrete_map=colour_map,
                     labels={"severity": "Severity", "count": "Event Count"},
                     height=220, template="plotly_dark")
    fig_sev.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                          showlegend=False, margin=dict(l=40, r=20, t=20, b=40))
    st.plotly_chart(fig_sev, use_container_width=True)

    # Event table with HTML badges
    st.markdown('<div class="section-header">Event Log</div>', unsafe_allow_html=True)

    def sev_badge(s):
        return f'<span class="badge-{s}">{s.upper()}</span>'

    def res_badge(r):
        return ('<span style="color:#22c55e">✅ Resolved</span>'
                if r else '<span style="color:#ef4444">🔴 Open</span>')

    disp = filtered.copy()
    disp["severity"] = disp["severity"].apply(sev_badge)
    disp["resolved"] = disp["resolved"].apply(res_badge)
    disp = disp[["id", "timestamp", "event_type", "node_id", "severity", "message", "resolved"]]
    disp.columns = ["ID", "Timestamp", "Event Type", "Node", "Severity", "Message", "Status"]
    st.markdown(disp.to_html(escape=False, index=False), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — NODE DETAIL
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Node Detail":
    st.title("🔍 Node Detail")
    st.markdown("Full drill-down view for a selected mesh node.")
    st.divider()

    node_ids = [n["node_id"] for n in NODE_DEFINITIONS]
    sel_node = st.selectbox("Select Node", node_ids, index=0)

    # Node info card
    nodes_df = get_nodes_df()
    node_row = nodes_df[nodes_df["node_id"] == sel_node].iloc[0]
    STATUS_EMOJI = {"online": "🟢", "offline": "🔴", "degraded": "🟡"}

    st.markdown(f"""
    <div class="kpi-card" style="text-align:left; padding: 24px 32px; margin-bottom:24px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:22px; font-weight:700; color:#f1f5f9;">{STATUS_EMOJI.get(node_row['status'], '⚪')} {node_row['node_id']}</div>
                <div style="color:#94a3b8; margin-top:4px;">{node_row['location']}</div>
            </div>
            <span class="badge-{node_row['status']}">{node_row['status'].upper()}</span>
        </div>
        <hr style="border-color:#334155; margin:16px 0;">
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:16px;">
            <div><div class="kpi-label">IP Address</div><div style="color:#e2e8f0; font-weight:600;">{node_row['ip_address']}</div></div>
            <div><div class="kpi-label">Hop Count</div><div style="color:#e2e8f0; font-weight:600;">{node_row['hop_count']}</div></div>
            <div><div class="kpi-label">Battery</div><div style="color:#e2e8f0; font-weight:600;">{node_row['battery_level']}</div></div>
            <div><div class="kpi-label">Last Seen</div><div style="color:#e2e8f0; font-weight:600;">{node_row['last_seen']}</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics & Sensor Charts side by side
    mc, sc = st.columns(2)
    with mc:
        st.markdown('<div class="section-header">RSSI (Last 24h)</div>', unsafe_allow_html=True)
        mdf = get_metrics_df(sel_node, 24)
        fig_m = px.line(mdf, x="timestamp", y="rssi",
                        color_discrete_sequence=["#38bdf8"],
                        height=240, template="plotly_dark",
                        labels={"rssi": "RSSI (dBm)", "timestamp": ""})
        fig_m.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                            margin=dict(l=30, r=10, t=10, b=30))
        st.plotly_chart(fig_m, use_container_width=True)

    with sc:
        st.markdown('<div class="section-header">Temperature (Last 24h)</div>', unsafe_allow_html=True)
        sdf = get_sensor_df(sel_node, 24)
        fig_s = px.line(sdf, x="timestamp", y="temperature",
                        color_discrete_sequence=["#f97316"],
                        height=240, template="plotly_dark",
                        labels={"temperature": "Temp (°C)", "timestamp": ""})
        fig_s.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                            margin=dict(l=30, r=10, t=10, b=30))
        st.plotly_chart(fig_s, use_container_width=True)

    # Recent metrics table
    t1, t2 = st.columns(2)
    with t1:
        st.markdown('<div class="section-header">Last 10 Metric Readings</div>', unsafe_allow_html=True)
        mdf_tail = mdf.tail(10)[["timestamp", "rssi", "latency_ms", "packet_loss", "throughput"]].copy()
        mdf_tail["timestamp"] = mdf_tail["timestamp"].dt.strftime("%H:%M")
        mdf_tail.columns = ["Time", "RSSI", "Latency (ms)", "Pkt Loss (%)", "Throughput (kbps)"]
        st.dataframe(mdf_tail, use_container_width=True, hide_index=True)

    with t2:
        st.markdown('<div class="section-header">Last 10 Sensor Readings</div>', unsafe_allow_html=True)
        sdf_tail = sdf.tail(10)[["timestamp", "temperature", "humidity"]].copy()
        sdf_tail["timestamp"] = sdf_tail["timestamp"].dt.strftime("%H:%M")
        sdf_tail.columns = ["Time", "Temp (°C)", "Humidity (%)"]
        st.dataframe(sdf_tail, use_container_width=True, hide_index=True)

    # Node-specific alert history
    st.markdown('<div class="section-header">Alert History for this Node</div>', unsafe_allow_html=True)
    events_df = get_events_df()
    node_events = events_df[events_df["node_id"] == sel_node]

    if node_events.empty:
        st.info("No events recorded for this node.")
    else:
        def sev_badge(s):
            return f'<span class="badge-{s}">{s.upper()}</span>'
        def res_badge(r):
            return '<span style="color:#22c55e">✅</span>' if r else '<span style="color:#ef4444">🔴</span>'

        disp = node_events.copy()
        disp["severity"] = disp["severity"].apply(sev_badge)
        disp["resolved"] = disp["resolved"].apply(res_badge)
        disp = disp[["timestamp", "event_type", "severity", "message", "resolved"]]
        disp.columns = ["Timestamp", "Event Type", "Severity", "Message", "Status"]
        st.markdown(disp.to_html(escape=False, index=False), unsafe_allow_html=True)
