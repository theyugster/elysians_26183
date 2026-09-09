# ChainTrace-I4C: Graph ML Fraud Detection & Culprit KYC Intelligence Engine

> **Smart India Hackathon (SIH 2026)**  
> **Dataset:** Elliptic++ Bitcoin Blockchain Transaction Dataset (5,000 transactions, 183 features)  
> **Model:** Random Forest Ensemble + Graph Topological Features (PageRank, HITS, Degree Centrality)  
> **Legal Framework:** BNSS Section 94 Digital Evidence Order Architecture

---

## 1. System Architecture Overview

ChainTrace-I4C is an advanced cryptocurrency forensic intelligence platform that loads and evaluates the **Elliptic++ dataset** — a real-world Bitcoin blockchain transaction graph — using a **Graph Machine Learning Engine**. It scores every transaction using a Random Forest classifier trained on 183 Elliptic features plus 8 graph-topological features, detects fraudulent wallets, and performs **KYC Unmasking** to link on-chain culprit wallets to real-world identities.

```
┌──────────────────────────────────────────────────────────────────┐
│                    ChainTrace-I4C Architecture                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐  │
│  │  Elliptic++      │    │  Graph ML Engine                     │  │
│  │  Dataset         │───>│  • Random Forest Classifier          │  │
│  │  (3 CSV files)   │    │  • PageRank / HITS / Centrality      │  │
│  │  + Wallet Map    │    │  • 183 + 8 features per transaction  │  │
│  │  + KYC Records   │    │  • Fraud probability scoring         │  │
│  └─────────────────┘    └──────────────┬──────────────────────┘  │
│                                          │                         │
│  ┌─────────────────┐    ┌──────────────┴──────────────────────┐  │
│  │  FastAPI Backend │<───│  Scored Transactions & Culprits      │  │
│  │  (REST API)      │    │  • 5,000 txs scored                  │  │
│  │                  │    │  • ~71 culprit wallets flagged        │  │
│  └────────┬────────┘    │  • KYC resolution for each            │  │
│           │              └─────────────────────────────────────┘  │
│  ┌────────┴────────┐                                              │
│  │  React Frontend  │                                              │
│  │  (Vite + Canvas) │                                              │
│  │  • Graph Canvas   │                                              │
│  │  • KYC Panel      │                                              │
│  │  • Tx Feed        │                                              │
│  └─────────────────┘                                              │
└──────────────────────────────────────────────────────────────────┘
```

```

---

## 2. SIH 2026 Upgrades (New Features)

The following elite features were engineered specifically to win SIH 2026, satisfying strict legal compliance, operational reality, and AI explainability constraints:

1. **Dual-Tier Cache Architecture**: Defends the "sub-10-second" traversal claim by caching known VASP wallets locally in memory (Tier 1), ensuring that O(n) BFS traversal (Tier 2) avoids slow database/RPC lookups for exchange identification.
2. **Configurable Hop Limits**: BFS traversal defaults to 5 hops (based on empirical evidence that >90% of laundered funds hit an exchange within 5 hops) but is dynamically configurable up to 10 hops for complex layering schemes.
3. **Value Continuity Check**: Protects innocent co-depositors in exchange pools. If the amount arriving at the terminal off-ramp is drastically higher (>20%) than the victim outflow, the system flags a "High Merge Risk" warning to prevent blanket freeze orders on the entire wallet.
4. **XGBoost ML Attribution & SHAP**: Brittle rules are replaced with tabular feature extraction and an XGBoost Mock. Crucially, the UI renders the SHAP explainability (Top AI Contributing Features) so Investigating Officers understand *why* the model made its decision.
5. **Confidence Threshold Gating**: Enforces BNSS Sec 94 compliance:
   - **≥85% Confidence & 3 Signals**: Auto-generates BNSS Sec 94 draft.
   - **60-84% Confidence**: Flagged for Senior IO Review (amber alert).
   - **<60% Confidence**: Dead End (red alert) — mandates manual cyber forensics.
6. **Chain Break Detection**: Explicitly identifies non-custodial protocols (Mixers, Tornado Cash, DeFi DEXs). Instead of failing silently, the UI flashes a red alert: "Chain Break Detected - Escalate to Manual Investigation."
7. **Unknown VASP Escalation**: If exchange behavioral patterns are detected but the identity is not in the registry, the system pivots from a BNSS-94 freeze order to an "Export FIU-IND Escalation Request".
8. **Watchlist Mode**: Evolves the system from reactive to proactive. IOs can add suspected mule wallets to a watchlist; if funds move into those wallets, a background alert is triggered automatically.
9. **Human-In-The-Loop (HITL) Safeguard**: The BNSS Sec 94 "Generate" button is physically disabled until the IO explicitly checks two boxes: confirming review of AI evidence, and applying a digital signature.

---

## 2. Dataset: Elliptic++ Format

### What is Elliptic++?

The [Elliptic++ dataset](https://github.com/git-disl/EllipticPlusPlus) is a graph network of **203,769 real Bitcoin blockchain transactions** and **822,942 wallet addresses** created by researchers at Georgia Tech. It is the standard benchmark for graph-based cryptocurrency fraud detection.

### Our Dataset (Synthetic Subset)

Since the full dataset is hosted on Google Drive (~1.5GB) and cannot be auto-loaded, this project ships with a **5,000-transaction synthetic subset** that faithfully mirrors the Elliptic++ format:

| File | Description | Rows |
|---|---|---|
| `txs_features.csv` | 183 features per transaction (166 Elliptic + 17 local) | 5,000 |
| `txs_classes.csv` | Ground-truth labels: 1=illicit, 2=licit, 3=unknown | 5,000 |
| `txs_edgelist.csv` | Directed money-flow edges between transactions | 1,405 |
| `wallets_map.csv` | Maps transaction IDs to from/to wallet addresses | 5,000 |
| `kyc_records_elliptic.json` | Synthetic KYC records for flagged wallets | 48 |

### Class Distribution

| Class | Label | Count | Percentage |
|---|---|---|---|
| 1 | **Illicit** (fraud, darknet, theft) | ~110 | 2.2% |
| 2 | **Licit** (legitimate transfers) | ~1,030 | 20.6% |
| 3 | **Unknown** (unlabeled) | ~3,860 | 77.2% |

### How to Replace with Real Elliptic++ Data

1. Download the real dataset from [Google Drive](https://drive.google.com/drive/folders/1MRPXz79Lu_JGLlJ21MDfML44dKN9R08l)
2. Place `txs_features.csv`, `txs_classes.csv`, and `txs_edgelist.csv` in `backend/data/`
3. Generate a wallet mapping: Create a `wallets_map.csv` with columns `[txId, from_wallet, to_wallet, amount_btc, timestamp]`
4. Restart the backend — the model will retrain on the full dataset

---

## 3. Graph ML Model

### Architecture

The fraud detection model uses a **hybrid approach**:

1. **Elliptic Features (183)**: The 166 original Elliptic features (transaction amounts, fees, timing, input/output counts) plus 17 Elliptic++ local features (degree centrality, clustering coefficient, flow velocity, etc.)

2. **Graph Topological Features (8)**: Computed from the transaction edge graph using NetworkX:
   - PageRank (flow centrality)
   - HITS Hub & Authority scores
   - Degree centrality
   - In-degree & Out-degree
   - Fan-in / Fan-out ratios

3. **Random Forest Classifier**: Trained on the labeled subset (illicit class 1 vs licit class 2):
   - 100 estimators, max depth 12
   - Balanced class weights to handle 10:1 class imbalance
   - StandardScaler normalization

### Scoring Pipeline

```
txs_features.csv ─┐
                    ├─> Merge ─> Add Graph Features ─> Train RF ─> Score ALL 5,000 txs
txs_classes.csv  ─┘                                     │
txs_edgelist.csv ─> NetworkX Graph ─> PageRank/HITS ────┘
                                                          │
                                                    ┌─────┴─────┐
                                                    │ fraud_score │
                                                    │ (0-100)     │
                                                    └─────────────┘
                                                          │
                                              >=70: FRAUDULENT
                                              40-69: SUSPICIOUS
                                               <40: LEGITIMATE
```

### Risk Factors

Each transaction receives human-readable risk factor explanations:
- Ground-truth illicit labels from Elliptic++
- Anomalous transaction volume
- High output concentration (layering indicator)
- Rapid forward ratio (automated sweeper)
- High PageRank centrality (hub node)
- Fan-in convergence (consolidation pattern)
- Sybil cluster scoring

---

## 4. KYC Resolution

After the model flags culprit wallets, the **KYC Resolver** attempts to unmask real-world identities:

1. **Direct KYC Match**: If the wallet has a registered KYC record (exchange, verified user)
2. **Downstream Path Tracing**: For unhosted mule wallets, traces the transaction graph downstream to find the terminal off-ramp where KYC is registered

KYC records include: Full name, National ID (Aadhaar/Passport), Bank accounts (with IFSC/SWIFT), IP addresses, Physical address, Email, Phone.

> **Note:** KYC records in this demo are **synthetically generated** to simulate realistic forensic intelligence. In production, these would be sourced from VASP compliance databases.

---

## 5. How to Run

### Prerequisites

- Python 3.11+
- Node.js 18+
- pip

### Step 1: Generate Dataset (Optional — already included)

```bash
cd backend
python data/generate_elliptic_dataset.py
```

This generates the 5,000-transaction Elliptic++ format dataset in `backend/data/`.

### Step 2: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will:
- Load the Elliptic++ dataset (3 CSV files)
- Build the NetworkX transaction graph
- Train the Random Forest classifier on labeled data
- Score all 5,000 transactions
- Flag ~71 culprit wallets
- Resolve KYC for each culprit

### Step 4: Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Step 5: Start Frontend Dev Server

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

---

## 6. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/graph-ml/dataset/load` | Load/reload the Elliptic++ dataset |
| `GET` | `/api/graph-ml/dataset/status` | Current dataset status & metrics |
| `GET` | `/api/graph-ml/dataset/info` | Detailed Elliptic++ statistics |
| `GET` | `/api/graph-ml/analyze?target=tx_1&hops=3` | Graph ML analysis from target |
| `GET` | `/api/graph-ml/transactions/scored?min_score=0&limit=500` | Scored transactions feed |
| `GET` | `/api/graph-ml/culprits/identified` | All culprit wallets with KYC |
| `GET` | `/api/graph-ml/wallet/{address}/kyc` | KYC resolution for a wallet |
| `POST` | `/api/forensics/dossier/generate` | Generate BNSS-94 legal order |

---

## 7. Project Structure

```
boowomp/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── graph_fraud.py      # Graph ML & KYC API routes
│   │   │   └── forensics.py        # BNSS legal order generation
│   │   ├── engine/
│   │   │   ├── graph_model.py      # Random Forest + Graph ML Engine
│   │   │   └── kyc_resolver.py     # KYC Intelligence Resolver
│   │   ├── schemas/
│   │   │   └── graph_fraud.py      # Pydantic response models
│   │   └── main.py                 # FastAPI application entry
│   ├── data/
│   │   ├── txs_features.csv        # Elliptic++ features (5,000 × 185)
│   │   ├── txs_classes.csv         # Ground-truth labels
│   │   ├── txs_edgelist.csv        # Transaction edge graph
│   │   ├── wallets_map.csv         # Tx-to-wallet mapping
│   │   ├── kyc_records_elliptic.json # Synthetic KYC records
│   │   └── generate_elliptic_dataset.py  # Dataset generator script
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main React application
│   │   ├── components/
│   │   │   ├── RealtimeGraphCanvas.jsx
│   │   │   ├── CulpritKYCPanel.jsx
│   │   │   ├── ScoredTransactionsFeed.jsx
│   │   │   ├── EntityInspector.jsx
│   │   │   ├── DossierModal.jsx
│   │   │   └── ErrorBoundary.jsx
│   │   └── services/
│   │       └── api.js              # API client
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 8. References

- **Elliptic++ Dataset**: Youssef Elmougy, Ling Liu. "Elliptic++ Dataset: A Graph Network of Bitcoin Blockchain Transactions and Wallet Addresses." Georgia Institute of Technology. [GitHub](https://github.com/git-disl/EllipticPlusPlus)
- **Original Elliptic Dataset**: Weber et al., "Anti-Money Laundering in Bitcoin: Experimenting with Graph Convolutional Networks for Financial Forensics," KDD 2019 Workshop.
- **BNSS**: Bharatiya Nagarik Suraksha Sanhita (2023), Section 94 — Digital Evidence Requisition Order.
