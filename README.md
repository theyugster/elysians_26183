# ChainTrace-I4C: Automated Blockchain Forensics & Off-Ramp Intelligence Engine

> **Smart India Hackathon (SIH 2026)**  
> **Problem Statement:** Automated Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges via Automated Blockchain Analytics.  
> **Legal Mandate:** Bharatiya Nagarik Suraksha Sanhita (BNSS) Section 94 Digital Evidence Order Architecture.

---

## Architecture Overview

ChainTrace-I4C is an end-to-end, production-ready cryptocurrency forensic tracing platform designed for law enforcement agencies (LEAs) and Cyber Crime Investigating Officers (IOs). It ingests multi-hop blockchain topologies, identifies intermediary layering mules, detects automated sweeper bot consolidation hubs, and flags terminal centralized exchanges (VASPs) for immediate account freeze and KYC requisition.

```
                  ┌────────────────────────────────────────────────────────┐
                  │          ChainTrace-I4C Forensics Engine               │
                  └─────────────────────────┬──────────────────────────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
   [5-Hop BFS Traversal]       [4-Signal Attribution]        [BNSS-94 Dossier]
    • Value-pruned (<3%)        • Known VASP Registry         • SHA-256 Audit Seal
    • Multi-path layering       • Sweeper Bot Detection       • Auto-KYC Demand
    • Topology reconstruction   • Gas Sponsor Profiling       • Court-Admissible
                                • Fan-In Reconvergence
```

---

## Where the Test Data Is & How It Works

### 1. Test Data File Locations
The test scenario data is maintained and pre-seeded in the following codebase files:

| Component | File Path | Description |
|---|---|---|
| **Auto-Seed Function** | [`backend/app/main.py`](file:///c:/Users/yugen/Desktop/boowomp/backend/app/main.py) | `seed_demo_blockchain_data()` initializes all VASP registries, wallets, and multi-hop transactions on application startup if the database is empty. |
| **Alembic Initial Migration** | [`backend/alembic/versions/0001_initial_schema.py`](file:///c:/Users/yugen/Desktop/boowomp/backend/alembic/versions/0001_initial_schema.py) | Defines the PostgreSQL DDL schema (`wallets`, `transactions`, `vasp_registry`, `requisitions`). |
| **Verification Test Suite** | [`backend/tests/test_backend.py`](file:///c:/Users/yugen/Desktop/boowomp/backend/tests/test_backend.py) | Seeds an in-memory test database and validates the entire 5-hop topology, heuristics, and API responses. |
| **Frontend Demo Fallback** | [`frontend/app.js`](file:///c:/Users/yugen/Desktop/boowomp/frontend/app.js) | Holds `DEMO_FALLBACK_DATA` mirroring the seed topology, ensuring the UI remains interactive even when the backend is offline. |

---

### 2. How the Test Data Works (Topology & Mechanics)

The testnet dataset models a realistic cyber fraud case where funds are exfiltrated from a victim and layered through multiple mule hops to evade law enforcement before hitting an offshore exchange:

```
[0xVic_9011] (Victim Origin)
    │
    ├── (48,500 USDT, Latency: 42s) ──────────────────────────► [0xMule_A1] (Hop 1 Mule)
    │                                                                │
    │                                        ┌───────────────────────┴───────────────────────┐
    │                                        │ (24,000 USDT, Latency: 18s)                   │ (23,800 USDT, Latency: 22s)
    │                                        ▼                                               ▼
    │                                  [0xMule_A2] (Hop 2)                             [0xMule_B1] (Hop 2)
    │                                        │                                               │
    │                                        │ (23,950 USDT, Latency: 12s)                   │ (23,720 USDT, Latency: 15s)
    │                                        └───────────────────────┬───────────────────────┘
    │                                                                ▼
    │                                                      [0xConsol_99] (Hop 3 Fan-In Consolidation)
    │                                                                │
    │                                                                │ (47,500 USDT, Latency: 8s)
    │                                                                ▼
    │                                                      [0xVASP_GlobalEx] (Hop 4 Terminal VASP)
    │                                                      "CryptoGlobal Exchange (Hot Wallet 04)"
    │
    └── (700 USDT, Latency: 120s) ──► [0xDust_Pruned] (Dusted <3% ──► PRUNED AUTOMATICALLY!)
```

#### Detailed Entity Roles & Heuristics Breakdown

1. **Victim Origin Wallet (`0xVic_9011`)**
   - **Role**: Origin point where unauthorized exfiltration occurred.
   - **Initial Balance**: `120.50 USDT`. Total outbound stolen funds: `49,200.00 USDT`.
   - **Baseline Risk Score**: `5 / 100`.

2. **Layering Mules (`0xMule_A1`, `0xMule_A2`, `0xMule_B1`)**
   - **Hop 1 (`0xMule_A1`)**: Splits the $48,500 stream into two parallel branches: $24,000 to `0xMule_A2` and $23,800 to `0xMule_B1`.
   - **Hop 2 (`0xMule_A2` & `0xMule_B1`)**: Rapid forwarding nodes with forward ratios `> 98%`.
   - **Threat Scores**: `68 - 82 / 100`.

3. **Consolidation Hub (`0xConsol_99`)**
   - **Role**: Mule consolidation node where split funds reconverge before off-ramping.
   - **Fan-In Score**: **`96%`** (due to in-degree $\ge 2$ and low out-degree to VASP).
   - **Sweeper Score**: **`95%`** (funds forwarded in $\le 12$ seconds).
   - **Threat Score**: **`92 / 100`**.

4. **Terminal Off-Ramp VASP (`0xVASP_GlobalEx`)**
   - **Exchange Name**: `CryptoGlobal Exchange (Hot Wallet 04)`.
   - **Jurisdiction**: `Seychelles / Non-Compliant`.
   - **Compliance**: `False` (uncooperative offshore exchange).
   - **VASP Match**: **`100%`** (exact match in `vasp_registry` table).
   - **Composite Threat Score**: **`97 / 100`**.

5. **Dust Pruning Filter (<3%) with `0xDust_Pruned`**
   - **The Problem**: Attackers often send micro-dust transactions ($1 to $50) to hundreds of random wallets to create noise and crash forensic graph visualizers.
   - **The Solution**: ChainTrace-I4C calculates the root stolen amount ($49,200 USDT). The pruning threshold is set to `3.0%` ($1,476 USDT).
   - **The Result**: The 700 USDT transfer to `0xDust_Pruned` ($1.42\% < 3.0\%$) is automatically pruned from the final graph. The response reflects `"prunedDustBranches": 1`.

6. **Gas Sponsor Profiling with `0xGasSponsor_Sybil`**
   - **Role**: Mule wallets typically do not possess native gas tokens (e.g., TRX/ETH) to pay network fees.
   - **The Heuristic**: An unlinked sponsor wallet (`0xGasSponsor_Sybil`) funds gas for transactions across `0xMule_A1`, `0xMule_A2`, and `0xMule_B1`.
   - **The Result**: The heuristic engine links these physically separate addresses into a single Sybil crime cluster with a Gas Sponsor Score of **`95%`**.

---

## How to Run the System

### Option 1: Docker Compose (Recommended)

From the root directory or `backend/` directory:

#### Run in Background (Detached Mode):
```bash
cd backend
docker compose up -d --build
```

#### Run in Foreground (Live Logs View):
```bash
cd backend
docker compose up --build
```

#### What Docker Compose Does Automatically:
1. Boots `chaintrace_postgres` (PostgreSQL 16) and waits for its health check (`pg_isready`).
2. Boots `chaintrace_redis` (Redis 7).
3. The `api` container runs [`entrypoint.sh`](file:///c:/Users/yugen/Desktop/boowomp/backend/entrypoint.sh):
   - Polls PostgreSQL socket on port 5432 until ready.
   - Executes Alembic migrations (`alembic upgrade head`) to construct tables.
   - Starts FastAPI with Uvicorn on `0.0.0.0:8000`.
   - Lifespan hook triggers `seed_demo_blockchain_data()`.

#### Useful Docker Commands:
```bash
# Check container status
docker compose ps

# View live API logs
docker compose logs -f api

# Stop all containers
docker compose down
```

---

### Option 2: Run Locally (Native Python Virtual Environment)

If you wish to run the backend natively on your machine without Docker:

#### 1. Install Dependencies:
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

#### 2. Configure Environment:
Create a `.env` file in `backend/` (or use default environment settings):
```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chaintrace_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev_secret_key
```

#### 3. Run Database Migrations:
```bash
alembic upgrade head
```

#### 4. Start the FastAPI Server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Option 3: Run the Automated Verification Test Suite

You can run the comprehensive self-contained test suite at any time (uses an in-memory async SQLite engine with no external database dependencies required):

```bash
cd backend
python tests/test_backend.py
```

Expected output:
```
--- Starting ChainTrace-I4C Backend Verification Suite ---

1. Testing Multi-Signal Heuristic Matrix...
   [PASS] Sweeper scoring heuristics verified.
   [PASS] Gas sponsor profiling heuristics verified.
   [PASS] Fan-In topology heuristics verified.
   [PASS] Composite threat index computation verified.

2. Initializing SQLite In-Memory Database and Tables...
   [PASS] Demo blockchain data seeded.

3. Testing 5-Hop BFS Traversal with Dust Pruning (<3%)...
   Nodes found: 6
   Links found: 6
   Terminal exchange: CryptoGlobal Exchange (Hot Wallet 04)
   Pruned dust branches: 1
   Traversal latency: 5.31 ms
   [PASS] 5-Hop BFS Traversal successfully identified off-ramp and pruned dust.

4. Testing FastAPI HTTP Endpoints via AsyncClient...
   [PASS] GET /health is online.
   [PASS] POST /api/auth/login authorized officer credentials.
   [PASS] POST /api/auth/login rejected unauthorized officer ID.
   [PASS] GET /api/forensics/trace returned valid ForensicTraceResponse.
   [PASS] POST /api/forensics/dossier/generate created Dossier BNSS-94-AB802FF70C.
   [PASS] GET /api/forensics/stats returned metrics.
   [PASS] GET /api/forensics/vasp-registry listed registered VASPs.
   [PASS] GET /api/forensics/wallet/{address} returned wallet profile.
   [PASS] GET /api/forensics/dossiers listed saved dossiers.

ALL 8/8 BACKEND VERIFICATION CHECKS PASSED SUCCESSFULLY!
```

---

## How to Run the Real-Time Predominantly White React UI

The frontend is located in [`frontend/`](file:///c:/Users/yugen/Desktop/boowomp/frontend/). It is a high-performance **React 19 + Vite** single-page application featuring a real-time force-directed graph canvas, animated transaction pulse streams, interactive node dragging, and live dust pruning controls.

### Launching the Frontend:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server will start at: **[http://localhost:3000](http://localhost:3000)**

### Real-Time UI Capabilities:
- **Interactive Force Simulation & Physics**: Nodes naturally position themselves according to BFS hop depth and spring physics. You can click and drag any node freely; it stretches its connections elastically and relaxes into position.
- **Live Fund Flow Particle Animation**: Animated particle pulses travel continuously along links from Victim $\to$ Mules $\to$ Consolidator $\to$ VASP, visually demonstrating the speed and direction of exfiltrated funds. Play, Pause, and adjust playback speed ($1\times, 2\times, 4\times$).
- **Dynamic Real-Time Dust Pruning Slider**: Adjust the dust threshold slider ($0.5\% - 5.0\%$) in real time. Sliding it down to $0.5\%$ dynamically un-prunes and displays the micro-dust branch (`0xDust_Pruned`); sliding it up above $1.0\%$ dynamically prunes and ghosts the branch.
- **Live Stream Synchronization Toggle**: Toggle "Live Sync" to auto-poll the FastAPI backend every 8 seconds for new blockchain blocks and graph updates.
- **Predominantly White Enterprise Theme**: Clean white surfaces (`#FFFFFF`), luminous subtle slate backgrounds (`#F8FAFC`), crisp borders (`#E2E8F0`), and Inter / JetBrains Mono typography.
- **Entity Threat Inspector**: Real-time gauge for the 4-Signal Attribution Matrix (VASP Match, Sweeper Score, Gas Sponsor, Fan-In).
- **BNSS Sec. 94 Legal Requisition Order Modal**: One-click generation of court-admissible digital freeze notices with a cryptographic SHA-256 integrity seal, confetti verification, and print/export capabilities.
- **Resilient Fallback**: Automatically connects to `http://localhost:8000/api`. If the backend is loading or offline, it seamlessly renders the full interactive testnet scenario in demo mode.

---

## API Endpoints Reference

Base URL: `http://localhost:8000`  
Swagger Interactive Documentation: `http://localhost:8000/docs`

| Method | Endpoint | Description | Sample Request / Query |
|---|---|---|---|
| `GET` | `/health` | System health check & feature list | N/A |
| `POST` | `/api/auth/login` | Investigating Officer authentication | `{"officerId": "IO-DELHI-402", "pin": "8841"}` |
| `GET` | `/api/forensics/trace` | Run 5-Hop BFS Traversal with dust filter | `?target=0xVic_9011` |
| `POST` | `/api/forensics/dossier/generate` | Generate BNSS Sec. 94 legal requisition | `{"officerId": "IO-402", "targetWallet": "0xVic_9011", "terminalExchange": "CryptoGlobal"}` |
| `GET` | `/api/forensics/stats` | High-level investigation metrics | N/A |
| `GET` | `/api/forensics/vasp-registry` | List registered centralized exchanges | N/A |
| `GET` | `/api/forensics/wallet/{address}` | Profile specific wallet risk & heuristics | Path: `/api/forensics/wallet/0xMule_A1` |
| `GET` | `/api/forensics/dossiers` | List historical BNSS evidence dossiers | N/A |

---

## Technical Stack

- **Backend Framework**: FastAPI 0.110+ (Python 3.11/3.13)
- **Database Engine**: PostgreSQL 16 with async driver `asyncpg` + SQLAlchemy 2.0 Async
- **Database Migrations**: Alembic 1.13+ (Async migrations)
- **Graph & Algorithms**: NetworkX 3.2+ (Directed BFS traversal & subgraph extraction)
- **Containerization**: Docker & Docker Compose
- **Frontend Architecture**: Pure HTML5, Vanilla CSS3 (Predominantly White Enterprise Design System), ES6+ JavaScript
# elysians_26183
Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges via Automated Blockchain Analytics
