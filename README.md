# Boho | Firewall Policy Simulation and Testing Platform

Boho is a cybersecurity web application for designing, simulating, auditing, and analyzing firewall rule policies against offline network traffic datasets.

> **Stage 3 Implementation Update:**
> Boho now includes **Stage 3: AI-Powered Security Assistant** powered by Amazon Bedrock (`amazon.nova-pro-v1:0`):
> - **Explain with AI**: In-depth explanations for findings (shadowed rules, redundancy, overly permissive configurations) detailing issue, evidence, risks, remediation, side effects, and verification.
> - **AI Rule Recommendations**: "Suggest Improvements" on the Firewall Rules page recommending safer rules with rationales and impact assessments.
> - **AI Policy Comparison**: "Explain Comparison with AI" analyzing before-and-after decisions, newly allowed/denied traffic, and areas of concern.
> - **Context-Aware AI Assistant**: Slide-out assistant drawer answering questions about your existing rules, findings, and comparisons.
> - **Dual-Theme Support**: Instant toggle between traditional Light Mode (white background, dark text) and Dark Mode (black background, light text).
> - **Safety & Determinism**: The evaluation and analysis engines remain 100% deterministic; all AI features are advisory and read-only. No AWS credentials are hardcoded.

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
 [ Evaluation & Analysis Engines ]    [ SQLAlchemy ORM ]
   ├── Firewall Evaluator (ipaddress)    ├── Rules & Simulations
   ├── Shadowing & Redundancy Detector   ├── Policy Analyses & Findings
   └── Policy Comparison Engine          └── Policy Comparison Snapshots
```

- **Evaluation Engine (`backend/app/engine/firewall_engine.py`)**: Standalone Python module implementing deterministic first-match-wins rule evaluation using Python's standard `ipaddress` library.
- **Analysis Engine (`backend/app/engine/policy_analyzer.py`)**: Mathematical traffic-space analyzer detecting full shadowing, behavioral redundancy, and security risks with transparent severity and remediations.
- **Comparison Engine (`backend/app/api/comparisons.py`)**: Re-evaluates identical recorded traffic packets against proposed policy modifications without mutating historical simulation sessions.
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
│   │   │   ├── dashboard.py      # Aggregated metrics & stats
│   │   │   ├── analysis.py       # Policy analysis, findings & dismissals (Stage 2)
│   │   │   └── comparisons.py    # Before-and-after policy comparison (Stage 2)
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── firewall_engine.py# Deterministic offline evaluation engine
│   │   │   └── policy_analyzer.py# Mathematical shadowing, redundancy & audit engine (Stage 2)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── firewall.py       # Rules, simulations, and snapshots models
│   │   │   └── analysis.py       # Analysis findings, comparisons & diff models (Stage 2)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── firewall.py       # Pydantic models for Stage 1
│   │   │   └── analysis.py       # Pydantic models for Stage 2
│   │   ├── database.py           # SQLite connection & session maker
│   │   ├── main.py               # FastAPI entrypoint & CORS setup
│   │   └── seed.py               # Default rule seeder script
│   ├── tests/
│   │   ├── test_engine.py        # Evaluation engine unit tests
│   │   ├── test_api.py           # REST API & historical snapshot tests
│   │   ├── test_dataset.py       # CSV validation & parsing tests
│   │   ├── test_shadowing.py     # Rule shadowing detection tests (Stage 2)
│   │   ├── test_redundancy.py    # Rule redundancy detection tests (Stage 2)
│   │   ├── test_security_audit.py# Security risk detection tests (Stage 2)
│   │   └── test_comparison.py    # Policy comparison workflow tests (Stage 2)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx        # Top banner with offline safety badge
│   │   │   ├── Sidebar.jsx       # Tabbed navigation (including Stage 2 views)
│   │   │   ├── RuleModal.jsx     # Rule create/edit modal with validation
│   │   │   ├── RecordDetailModal.jsx # Per-packet diagnostics modal
│   │   │   ├── SnapshotModal.jsx # Historical rule snapshot inspector
│   │   │   ├── FindingDetailModal.jsx# Policy finding inspection & dismissal (Stage 2)
│   │   │   └── DeleteConfirmModal.jsx# Safe confirmation dialog
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx     # Recharts KPIs, charts, and activity
│   │   │   ├── FirewallRules.jsx # Rule list, toggles, priority reordering
│   │   │   ├── DatasetTesting.jsx# CSV upload, preview & simulation launch
│   │   │   ├── SimulationResults.jsx# Paginated traffic log, search & filter
│   │   │   ├── SimulationHistory.jsx# Historical sessions list
│   │   │   ├── PolicyAnalysis.jsx# Rule shadowing, redundancy & audit findings (Stage 2)
│   │   │   └── PolicyComparison.jsx# Before-and-after policy comparison (Stage 2)
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
| `POST` | `/api/analysis/run` | Execute formal rule shadowing, redundancy & security audit |
| `GET` | `/api/analysis/latest` | Retrieve most recent policy analysis report |
| `GET` | `/api/analysis` | List historical policy analyses |
| `GET` | `/api/analysis/{id}` | Get policy analysis detail, rule snapshot & findings |
| `PATCH` | `/api/analysis/findings/{id}/dismiss` | Dismiss a security finding with justification reason |
| `PATCH` | `/api/analysis/findings/{id}/restore` | Restore a dismissed security finding |
| `POST` | `/api/comparisons` | Create a Before-and-After policy comparison against a simulation |
| `GET` | `/api/comparisons` | List historical policy comparisons |
| `GET` | `/api/comparisons/{id}` | Get comparison metrics, diff breakdown & paginated records |
| `GET` | `/api/comparisons/{id}/export` | Export comparison results to CSV |
| `DELETE` | `/api/comparisons/{id}` | Delete a comparison record |


---

## Limitations (Stage 1 Scope)

1. **Offline Only**: Simulates packet decisions based on CSV logs. Live network interfaces, packet capture (PCAP/libpcap), and kernel packet filtering are intentionally excluded in Stage 1.
2. **Stateful Inspection**: Evaluates records statelessly per packet row. Connection state tracking (e.g., TCP 3-way handshake tracking, `ESTABLISHED,RELATED`) is planned for future stages.
3. **Dataset Limits**: Enforces a maximum file size of 5 MB and up to 10,000 rows per CSV upload to maintain responsive browser performance.
