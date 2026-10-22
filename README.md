# Boho | Firewall Policy Simulation and Testing Platform

Boho is a cybersecurity web application for designing, simulating, and auditing firewall rule policies against offline network traffic datasets.

> **Stage 1 Implementation Notice:**
> Boho is an offline, deterministic simulation and educational testing platform. It simulates packet routing decisions and **does not** modify the host operating system's firewall (iptables/nftables/pf), bind live network capture interfaces, or interfere with real traffic.

---

## Architecture Overview

Boho is engineered with a decoupled client-server architecture:

```
[ Frontend: React (JSX) + Vite + Tailwind CSS + Recharts ]
                            │ REST API (JSON)
                            ▼
      [ Backend: FastAPI (Python 3.13) + Pydantic v2 ]
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
 [ Evaluation Engine ]              [ SQLAlchemy ORM ]
   (ipaddress, first-match-wins)        (SQLite: boho.db)
```

- **Evaluation Engine (`backend/app/engine/firewall_engine.py`)**: A standalone, zero-dependency Python module implementing deterministic first-match-wins rule evaluation using Python's standard `ipaddress` library.
- **Rule Snapshots (`SimulationRuleSnapshot`)**: When running a simulation, active firewall rules are snapshotted into the database. Editing or deleting active rules later preserves historical simulation results.
- **Frontend (`frontend/src/`)**: Pure React (JSX, JavaScript) with a dark cybersecurity-themed dashboard styled with Tailwind CSS, Lucide icons, and Recharts.

---

## Directory Structure

```
Boho/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py       # Router registry
│   │   │   ├── rules.py          # Rule management REST endpoints
│   │   │   ├── datasets.py       # CSV dataset upload & validation
│   │   │   ├── simulations.py    # Simulation runner, detail & export
│   │   │   └── dashboard.py      # Aggregated metrics & stats
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   └── firewall_engine.py# Deterministic offline evaluation engine
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── firewall.py       # SQLAlchemy ORM database models
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── firewall.py       # Pydantic v2 request & response schemas
│   │   ├── database.py           # SQLite connection & session maker
│   │   ├── main.py               # FastAPI entrypoint & CORS setup
│   │   └── seed.py               # Default rule seeder script
│   ├── tests/
│   │   ├── test_engine.py        # 13 unit tests for evaluation engine
│   │   ├── test_api.py           # REST API & historical snapshot tests
│   │   └── test_dataset.py       # CSV validation & parsing tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx        # Top banner with offline safety badge
│   │   │   ├── Sidebar.jsx       # Tabbed navigation
│   │   │   ├── RuleModal.jsx     # Rule create/edit modal with validation
│   │   │   ├── RecordDetailModal.jsx # Per-packet diagnostics modal
│   │   │   ├── SnapshotModal.jsx # Historical rule snapshot inspector
│   │   │   └── DeleteConfirmModal.jsx# Safe confirmation dialog
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx     # Recharts KPIs, charts, and activity
│   │   │   ├── FirewallRules.jsx # Rule list, toggles, priority reordering
│   │   │   ├── DatasetTesting.jsx# CSV upload, preview & simulation launch
│   │   │   ├── SimulationResults.jsx# Paginated traffic log, search & filter
│   │   │   └── SimulationHistory.jsx# Historical sessions list
│   │   ├── api.js                # Frontend REST API client
│   │   ├── App.jsx               # Root application view
│   │   ├── main.jsx              # React DOM entrypoint
│   │   └── index.css             # Tailwind CSS & theme styling
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── vite.config.js
├── sample_traffic.csv            # Sample dataset for testing
└── README.md
```

---

## Setup & Running Instructions

### 1. Backend Setup

```bash
# In the project root:
# 1. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Seed default rules (optional but recommended)
PYTHONPATH=backend python backend/app/seed.py

# 4. Start the FastAPI development server (runs on http://127.0.0.1:8000)
PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive API documentation (Swagger UI) is available at:
`http://127.0.0.1:8000/docs`

### 2. Frontend Setup

In a separate terminal:

```bash
cd frontend

# 1. Install npm dependencies
npm install

# 2. Start the Vite development server (runs on http://127.0.0.1:5173)
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Running Automated Tests

Run the full pytest suite (covering the evaluation engine, dataset validation, and API snapshots):

```bash
source venv/bin/activate
PYTHONPATH=backend pytest backend/tests/ -v
```

All 24 test cases will execute:
- **`test_engine.py`**: ALLOW rules, DENY rules, first-match-wins, default DENY fallback, disabled rules, IP matching, CIDR range matching, port and port range matching, ANY wildcard matching, ICMP port handling, malformed record handling, and priority conflict resolution.
- **`test_api.py`**: Rule CRUD, rule validation, simulation execution, historical snapshot preservation when rules are modified/deleted, filtering, and CSV export.
- **`test_dataset.py`**: Sample CSV download, valid CSV preview, malformed row detection, fatal file errors (missing columns, non-CSV extension, empty file).

---

## Firewall Evaluation Logic & Protocols

### Priority Order (First-Match-Wins)
- Enabled rules are evaluated in ascending order of their `priority` integer (`1` is highest priority).
- Disabled rules are bypassed.
- Evaluation terminates at the first matching rule and returns that rule's action (`ALLOW` or `DENY`).
- If no enabled rule matches the traffic record, the engine enforces the default policy: **`DENY`**.

### Protocol and Port Matching Details
- **TCP / UDP**: Requires a destination port between `1` and `65535`, a range (e.g. `80-443`), or `ANY`.
- **ICMP**: ICMP operates at the network layer (OSI Layer 3) and does not utilize TCP/UDP port numbers. Destination ports are optional for ICMP records. If a rule specifies `ANY` port or no port, ICMP traffic matches.
- **ANY**: Matches any protocol or any port when explicitly designated. Blank inputs are disallowed and rejected to prevent unintended wildcard behaviors.

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check endpoint |
| `GET` | `/api/rules` | List all firewall rules sorted by priority |
| `POST` | `/api/rules` | Create a new firewall rule |
| `PUT` | `/api/rules/{id}` | Update an existing rule |
| `PATCH` | `/api/rules/{id}/toggle` | Toggle rule enabled/disabled status |
| `POST` | `/api/rules/reorder` | Batch update rule priorities |
| `DELETE` | `/api/rules/{id}` | Delete a rule |
| `POST` | `/api/rules/seed-defaults` | Seed standard cybersecurity baseline rules |
| `GET` | `/api/datasets/sample-csv` | Download sample CSV for testing |
| `POST` | `/api/datasets/upload-and-validate` | Upload and preview CSV dataset |
| `POST` | `/api/simulations` | Execute simulation against active rules |
| `GET` | `/api/simulations` | List simulation history |
| `GET` | `/api/simulations/{id}` | Get simulation detail, rule snapshot & paginated records |
| `GET` | `/api/simulations/{id}/export` | Export simulation records as downloadable CSV |
| `DELETE` | `/api/simulations/{id}` | Delete a simulation run |
| `GET` | `/api/dashboard/stats` | Aggregated dashboard metrics & distribution |

---

## Limitations (Stage 1 Scope)

1. **Offline Only**: Simulates packet decisions based on CSV logs. Live network interfaces, packet capture (PCAP/libpcap), and kernel packet filtering are intentionally excluded in Stage 1.
2. **Stateful Inspection**: Evaluates records statelessly per packet row. Connection state tracking (e.g., TCP 3-way handshake tracking, `ESTABLISHED,RELATED`) is planned for future stages.
3. **Dataset Limits**: Enforces a maximum file size of 5 MB and up to 10,000 rows per CSV upload to maintain responsive browser performance.
