# SignalSevak 📡

> **Self-Healing IoT Mesh Networking & Network Intelligence Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: ESP32](https://img.shields.io/badge/Platform-ESP32-green.svg)](https://www.espressif.com/)
[![Backend: Flask](https://img.shields.io/badge/Backend-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Dashboard: Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red.svg)](https://streamlit.io/)
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

---

## 📖 Overview

**SignalSevak** is an open-source IoT mesh networking and network intelligence platform engineered to provide **robust, resilient connectivity** in environments where traditional infrastructure fails. Designed for smart campuses, industrial floors, warehouses, and edge deployments, SignalSevak leverages a distributed ESP32 mesh network with a cloud-connected intelligence backend to monitor, visualize, and autonomously maintain network health — without any human intervention.

The platform transforms a collection of low-cost ESP32 nodes into a **self-organizing, self-healing communication fabric**, capable of routing around failures in real time and reporting granular analytics through a live dashboard.

---

## 🚨 Problem Statement

Modern IoT deployments consistently struggle with:

- **Dead zones** — areas where Wi-Fi or cellular signals fail to reach, causing total connectivity loss for sensors, actuators, and edge devices.
- **Single points of failure** — networks built around a central router or access point that, if compromised, take down entire segments.
- **Operational opacity** — no visibility into which nodes are failing, which paths are degraded, or what historical traffic patterns look like.
- **Manual recovery** — outages require physical intervention to reroute traffic or restore connectivity, resulting in costly downtime.

In environments like university campuses, factory floors, and agricultural fields, unresolved dead zones translate directly into data loss, compromised automation, and operational inefficiency.

---

## 💡 Solution Overview

SignalSevak addresses these challenges through two tightly integrated layers:

### 1. Self-Healing Mesh Network
A network of ESP32 nodes operates as a **multi-hop wireless mesh**. Each node maintains awareness of its neighbors and the overall topology. When a node or link fails, the mesh autonomously recalculates routing paths and reroutes all traffic within seconds — no reboot, no manual reconfiguration.

### 2. Network Intelligence Platform
A Flask-powered backend ingests continuous telemetry from every node — RSSI, packet loss, uptime, neighbor lists, and throughput. A Streamlit dashboard renders this data in real time as an interactive topology graph with health overlays, historical time-series analytics, and configurable alert rules.

Together, these layers give operators both **resilient infrastructure** and **actionable intelligence** over their entire deployment.

---

## ✨ Key Features

### 🔄 Self-Healing Mesh Networking
Nodes continuously exchange routing tables and health beacons. On link failure, neighbor nodes trigger local re-convergence within the mesh, transparently restoring data paths without operator involvement.

### 🔍 Automatic Node Discovery
Any ESP32 node broadcasting the SignalSevak mesh identifier is automatically discovered, authenticated, and incorporated into the routing topology. Zero-touch provisioning reduces deployment overhead.

### 📶 Dead-Zone Connectivity Bridging
Relay nodes act as transparent RF bridges between isolated subnet segments and the primary gateway, extending coverage into basements, stairwells, reinforced structures, and outdoor peripheries.

### 🗺️ Network Topology Visualization
The dashboard renders a live, interactive graph of all active nodes and their link states. Edge weights reflect current RSSI values; node colors indicate health status (healthy, degraded, offline).

### 💓 Node Health Monitoring
Per-node telemetry streams include:
- Signal strength (RSSI in dBm)
- Packet loss percentage
- CPU and memory utilization
- Uptime duration
- Hop count from gateway

### 🚨 Real-Time Alerts
Configurable threshold-based alerting triggers notifications when:
- A node goes offline
- RSSI drops below acceptable thresholds
- Packet loss exceeds defined limits
- Routing path length increases beyond baseline

### 📊 Historical Network Analytics
All telemetry is persisted to a time-series database. The analytics dashboard exposes trend graphs, anomaly markers, and exportable reports — enabling capacity planning, SLA validation, and predictive maintenance.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Dashboard Layer                          │
│                    Streamlit Web Application                     │
│         (Topology Graph · Health Monitor · Analytics)            │
└─────────────────────────┬────────────────────────────────────────┘
                          │ HTTP / WebSocket
┌─────────────────────────▼────────────────────────────────────────┐
│                         Backend Layer                            │
│                      Flask REST API                              │
│         (Telemetry Ingestion · Alert Engine · Data API)          │
└──────────────┬──────────────────────────────┬────────────────────┘
               │                              │
┌──────────────▼──────────┐    ┌─────────────▼──────────────────── ┐
│      Database Layer     │    │         Gateway Layer              │
│   SQLite / PostgreSQL   │    │    ESP32 Root Node (MQTT Broker)   │
│  (Time-series Telemetry)│    │   (Mesh ↔ IP Protocol Bridge)      │
└─────────────────────────┘    └─────────────┬──────────────────────┘
                                             │ ESP-MESH RF
              ┌──────────────────────────────▼──────────────────────┐
              │                     Node Layer                       │
              │     ESP32 Mesh Nodes (N ≥ 2)                        │
              │  · Multi-hop routing     · Telemetry broadcasting    │
              │  · Neighbor discovery    · Local relay buffering     │
              └─────────────────────────────────────────────────────┘
```

| Layer | Responsibility |
|---|---|
| **Node Layer** | Wireless mesh endpoints; collect sensor data, relay packets, broadcast telemetry beacons |
| **Gateway Layer** | Root ESP32 node; bridges ESP-MESH to IP network; hosts local MQTT broker |
| **Backend Layer** | Flask API; ingests telemetry, runs alert engine, exposes data endpoints |
| **Database Layer** | Persists all node telemetry and event logs for historical queries |
| **Dashboard Layer** | Streamlit app; real-time topology visualization, health monitoring, analytics |

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| **Mesh Nodes** | ESP32 (Espressif ESP-MESH / PainlessMesh library) |
| **Firmware Language** | C++ (Arduino Framework via PlatformIO) |
| **Gateway Protocol** | MQTT (Mosquitto broker on root node) |
| **Backend Framework** | Python · Flask |
| **Database** | SQLite (development) · PostgreSQL (production) |
| **ORM / Query Layer** | SQLAlchemy |
| **Dashboard** | Streamlit · Plotly · NetworkX |
| **Communication** | REST over HTTP · MQTT |
| **Alerting** | Custom threshold engine (extensible to PagerDuty / Slack webhooks) |
| **DevOps** | Docker · docker-compose |

---

## 🔄 Project Workflow / Data Flow

```
[Sensor / Device]
      │
      ▼
[ESP32 Mesh Node]  ──beacon──▶  [Neighbor Nodes]  (multi-hop relay)
      │
      │  telemetry payload (JSON over MQTT)
      ▼
[ESP32 Root / Gateway Node]
      │
      │  MQTT publish → Flask subscriber
      ▼
[Flask Backend]
  ├── Parses & validates telemetry
  ├── Writes to database (node_metrics table)
  ├── Evaluates alert thresholds
  └── Exposes /api/nodes, /api/metrics, /api/alerts endpoints
      │
      ▼
[Streamlit Dashboard]
  ├── Polls REST API (configurable interval)
  ├── Renders NetworkX topology graph
  ├── Overlays RSSI / health color coding
  └── Displays historical Plotly time-series charts
```

---

## 🔧 Hardware Components Required

| Component | Quantity | Notes |
|---|---|---|
| **ESP32 Development Board** | ≥ 3 | Any ESP32 variant (WROOM-32, WROVER, S3) |
| **USB-A to Micro-USB / USB-C cables** | Per node | For flashing and power |
| **Power supply / power bank** | Per node | 5V, ≥ 500 mA per board |
| **Breadboard + jumper wires** | Optional | For sensor attachment |
| **DHT22 / BME280 sensor** | Optional | Temperature / humidity demo payload |
| **PC or Raspberry Pi** | 1 | Hosts Flask backend and dashboard |

> **Minimum viable deployment:** 3 ESP32 nodes (1 root/gateway + 2 relay nodes).

---

## 🚀 Software Setup and Installation

### Prerequisites

- Python 3.9+
- Node.js (optional, for tooling)
- PlatformIO CLI (`pip install platformio`)
- Git

---

### 1. Clone the Repository

```bash
git clone https://github.com/Pranav-Dawange/hackarena26-template.git
cd hackarena26-template
```

---

### 2. Flash ESP32 Firmware

```bash
cd firmware
pio run --target upload --environment esp32dev
```

Edit `firmware/src/config.h` to set your mesh network name and password before flashing:

```cpp
#define MESH_SSID     "SignalSevak_Mesh"
#define MESH_PASSWORD "your_mesh_password"
#define MESH_PORT     5555
#define BACKEND_URL   "http://<backend-host>:5000/api/telemetry"
```

Flash the **root node** separately using the `root` build environment:

```bash
pio run --target upload --environment esp32dev_root
```

---

### 3. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Configure the environment:

```bash
cp .env.example .env
# Edit .env with your database URI, MQTT host, and alert thresholds
```

Initialize the database and start the server:

```bash
flask db upgrade
flask run --host=0.0.0.0 --port=5000
```

---

### 4. Dashboard Setup

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py -- --backend http://localhost:5000
```

Access the dashboard at `http://localhost:8501`.

---

### 5. Docker (Optional — Recommended for Production)

```bash
docker-compose up --build
```

Services started: Flask backend, PostgreSQL, Streamlit dashboard, and Mosquitto MQTT broker.

---

## 🕸️ How the Mesh Network Works

SignalSevak uses **ESP-MESH** (Espressif's layer-2 multi-hop wireless protocol) with the **PainlessMesh** Arduino library as the application-level abstraction.

1. **Bootstrapping:** On power-on, each node scans for a mesh SSID. The first node to not find a peer becomes the root and connects directly to the backend. Subsequent nodes join as children under the strongest available parent.

2. **Routing:** PainlessMesh maintains a full topology map across all nodes using a gossip-based protocol. Every node knows every other node's `nodeId` and shortest path.

3. **Data Relay:** A message originating on any leaf node is forwarded hop-by-hop toward the root, which bridges it to the IP network and publishes it to MQTT.

4. **Self-Healing:** Each node broadcasts a heartbeat every 10 seconds (configurable). If a parent node becomes unreachable, the child autonomously re-associates to the next-best parent within 5–15 seconds, with no data loss for buffered messages.

5. **Telemetry:** Every node periodically packages its RSSI to parent, hop count, uptime, and sensor readings into a JSON payload and routes it to the root for backend ingestion.

---

## 🎬 Demo Scenario: Node Failure and Automatic Rerouting

**Setup:** 4 ESP32 nodes — `Node-A` (root/gateway), `Node-B`, `Node-C`, `Node-D` (sensors).

**Baseline topology:**
```
[Node-D] ──► [Node-C] ──► [Node-B] ──► [Node-A (Root)] ──► Backend
```

**Failure event:** `Node-B` is powered off (simulating a hardware failure or signal obstruction).

**Expected behavior (< 15 seconds):**
1. `Node-C` detects loss of beacon from `Node-B`.
2. `Node-C` scans for alternate parents; discovers `Node-A` is within range.
3. `Node-C` re-associates directly to `Node-A`, updating the topology table.
4. `Node-D` detects `Node-C`'s topology update and confirms its own route remains valid through `Node-C` → `Node-A`.
5. Dashboard marks `Node-B` as **OFFLINE** (red), updates the topology graph to show the new direct link.

**Result:** Zero manual intervention. Data flow from `Node-D` resumes through the rerouted path within seconds.

---

## 🌍 Use Cases

| Domain | Application |
|---|---|
| **Smart Campus** | Connecting remote lecture halls, basements, gymnasium, and outdoor areas beyond Wi-Fi range |
| **Industrial Factory** | Monitoring machines across metal-shielded floors where Wi-Fi penetration is poor |
| **Warehouse / Logistics** | Asset tracking across large spaces with dense shelving that blocks RF |
| **Precision Agriculture** | Deploying sensor nodes across fields spanning hundreds of meters |
| **Disaster Response** | Rapid deployment of a temporary communication network in areas with destroyed infrastructure |
| **Smart Building / BMS** | Bridging floor-by-floor IoT sensors in buildings with poor vertical signal propagation |

---

## 🔮 Future Improvements

- **AI-Driven Network Prediction** — Train an LSTM model on historical telemetry to predict node failures before they occur, enabling pre-emptive rerouting.
- **Intelligent Node Placement Advisor** — Given a site floor plan and RSSI survey data, recommend optimal node positions to maximize coverage and minimize hop depth.
- **Advanced Routing Algorithms** — Implement OLSR or Dijkstra-aware quality-of-service routing that factors in link quality, packet loss, and latency alongside hop count.
- **FOTA (Firmware Over-The-Air) Updates** — Push firmware updates to all mesh nodes simultaneously from the dashboard without physical access.
- **End-to-End Encryption** — AES-256 payload encryption across mesh hops and TLS on all backend communications.
- **Mobile Application** — Native Android/iOS companion app for on-the-go monitoring and alert acknowledgement.
- **Multi-Gateway Support** — Deploy multiple root nodes connected to the backend for large-scale horizontal scaling.

---

## 🤝 Contribution Guidelines

Contributions are welcome and appreciated. Please follow these steps:

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes with clear, well-commented code.
3. Ensure all new code follows the existing style conventions and passes lint checks.
4. **Test** your changes locally and document any new configuration parameters in the relevant `README` or `.env.example`.
5. Open a **Pull Request** against the `main` branch with a clear description of the change and the problem it solves.

For significant changes or new features, please open an **Issue** first to discuss the proposal before investing time in implementation.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <sub>Built with ❤️ for resilient infrastructure · SignalSevak — <em>The Network That Heals Itself</em></sub>
</div>
