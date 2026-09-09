import asyncio
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.config import settings
from app.main import app, seed_demo_blockchain_data
from app.engine.graph_model import graph_model_engine

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

async def run_tests():
    print("--- Starting ChainTrace-I4C Backend Verification Suite ---")
    print("--- Elliptic++ Dataset Integration Tests ---\n")

    # 1. Test Graph Model Loading (Elliptic++ Format)
    print("1. Testing Elliptic++ Dataset Loading & Random Forest Training...")
    result = graph_model_engine.load_dataset()
    assert result["status"] == "LOADED", f"Dataset did not load: {result}"
    assert result["total_transactions"] >= 5000, f"Expected >= 5000 txs, got {result['total_transactions']}"
    assert result["unique_wallets"] >= 100, f"Expected >= 100 wallets, got {result['unique_wallets']}"
    assert result["graph_edges"] >= 100, f"Expected >= 100 edges, got {result['graph_edges']}"
    assert result["culprits_detected"] >= 10, f"Expected >= 10 culprits, got {result['culprits_detected']}"
    print(f"   [PASS] Loaded {result['total_transactions']} transactions, {result['unique_wallets']} wallets, {result['culprits_detected']} culprits.")

    # 2. Verify Scored Transactions
    print("\n2. Testing Transaction Scoring Pipeline...")
    scored_txs = graph_model_engine.scored_transactions
    assert len(scored_txs) >= 5000, f"Expected >= 5000 scored txs, got {len(scored_txs)}"

    # Verify fields
    sample_tx = scored_txs[0]
    required_fields = ["tx_hash", "from_address", "to_address", "amount", "fraud_score",
                       "fraud_probability", "classification", "risk_factors", "time_step", "elliptic_class"]
    for field in required_fields:
        assert field in sample_tx, f"Missing field '{field}' in scored transaction"

    # Verify classifications are valid
    valid_classes = {"FRAUDULENT", "SUSPICIOUS", "LEGITIMATE"}
    for tx in scored_txs[:100]:
        assert tx["classification"] in valid_classes, f"Invalid classification: {tx['classification']}"
        assert 0 <= tx["fraud_score"] <= 100, f"Invalid fraud_score: {tx['fraud_score']}"
        assert 0 <= tx["fraud_probability"] <= 1.0, f"Invalid fraud_probability: {tx['fraud_probability']}"
        assert len(tx["risk_factors"]) > 0, "Missing risk factors"

    fraud_txs = [t for t in scored_txs if t["classification"] == "FRAUDULENT"]
    susp_txs = [t for t in scored_txs if t["classification"] == "SUSPICIOUS"]
    legit_txs = [t for t in scored_txs if t["classification"] == "LEGITIMATE"]
    print(f"   [PASS] {len(scored_txs)} transactions scored: {len(fraud_txs)} FRAUDULENT, {len(susp_txs)} SUSPICIOUS, {len(legit_txs)} LEGITIMATE.")

    # 3. Verify Elliptic++ Fields
    print("\n3. Testing Elliptic++ Specific Fields...")
    for tx in scored_txs[:50]:
        assert tx["elliptic_class"] in [1, 2, 3], f"Invalid elliptic_class: {tx['elliptic_class']}"
        assert tx["time_step"] >= 1 and tx["time_step"] <= 49, f"Invalid time_step: {tx['time_step']}"

    illicit_txs = [t for t in scored_txs if t["elliptic_class"] == 1]
    licit_txs = [t for t in scored_txs if t["elliptic_class"] == 2]
    unknown_txs = [t for t in scored_txs if t["elliptic_class"] == 3]
    print(f"   [PASS] Elliptic++ classes: {len(illicit_txs)} illicit, {len(licit_txs)} licit, {len(unknown_txs)} unknown.")

    # 4. Verify Culprit Detection
    print("\n4. Testing Culprit Wallet Detection...")
    culprits = graph_model_engine.culprits
    assert len(culprits) >= 10, f"Expected >= 10 culprits, got {len(culprits)}"

    for c in culprits[:10]:
        assert "address" in c
        assert "threat_score" in c
        assert "role" in c
        assert c["is_culprit"] == True
        assert c["threat_score"] >= 55

    print(f"   [PASS] {len(culprits)} culprit wallets flagged (top score: {culprits[0]['threat_score']}).")

    # 5. Verify Dataset Info
    print("\n5. Testing Dataset Info...")
    info = graph_model_engine.get_dataset_info()
    assert info["total_transactions"] >= 5000
    assert info["num_features"] >= 183
    assert info["timesteps"] == 49
    assert "illicit" in info["class_distribution"]
    assert "licit" in info["class_distribution"]
    assert "unknown" in info["class_distribution"]
    print(f"   [PASS] Dataset info: {info['total_transactions']} txs, {info['num_features']} features, {info['timesteps']} timesteps.")

    # 6. Verify Subgraph Extraction
    print("\n6. Testing Subgraph Extraction...")
    # Use a wallet from the wallet map
    if not graph_model_engine.wallet_map_df.empty:
        test_wallet = graph_model_engine.wallet_map_df.iloc[0]["from_wallet"]
        subgraph = graph_model_engine.get_scored_subgraph(test_wallet, max_hops=2)
        assert len(subgraph["nodes"]) >= 1, "Subgraph should have at least 1 node"
        assert subgraph["target"] == test_wallet
        print(f"   [PASS] Subgraph extracted: {subgraph['total_nodes']} nodes, {subgraph['total_links']} links.")

    # 7. Setup In-Memory Database & Seed
    print("\n7. Initializing SQLite In-Memory Database...")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        from app.models.vasp import VASPRegistry
        from app.models.wallet import Wallet
        from app.models.transaction import Transaction

        vasp = VASPRegistry(
            exchange_name="CryptoGlobal Exchange (Hot Wallet 04)",
            hot_wallet_address="0xVASP_GlobalEx",
            network="TRC-20",
            jurisdiction="Seychelles / Non-Compliant",
            is_compliant=False
        )
        session.add(vasp)

        wallets = [
            Wallet(address="0xVic_9011", cluster_type="victim", balance=120.50, risk_score=5),
            Wallet(address="0xMule_A1", cluster_type="mule", balance=8400.00, risk_score=68),
            Wallet(address="0xVASP_GlobalEx", cluster_type="exchange", balance=1420000.00, risk_score=97),
        ]
        session.add_all(wallets)
        await session.flush()

        txs = [
            Transaction(tx_hash="0x71fb_a301", from_address="0xVic_9011", to_address="0xMule_A1", amount=48500.0, latency_seconds=42, gas_sponsor="0xGasSponsor_Sybil"),
            Transaction(tx_hash="0x10fe_ca41", from_address="0xMule_A1", to_address="0xVASP_GlobalEx", amount=47500.0, latency_seconds=8),
        ]
        session.add_all(txs)
        await session.commit()
    print("   [PASS] Demo blockchain data seeded.")

    # 8. HTTP API Endpoints Test
    print("\n8. Testing FastAPI HTTP Endpoints...")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Health check
        res = await client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        data = res.json()
        assert data["status"] == "online"
        print("   [PASS] GET /health is online.")

        # Auth Login - success
        auth_res = await client.post("/api/auth/login", json={"officerId": "IO-DELHI-402", "pin": "8841"})
        assert auth_res.status_code == 200, f"Login failed: {auth_res.text}"
        print("   [PASS] POST /api/auth/login authorized officer credentials.")

        # Dataset Status (Elliptic++)
        ds_res = await client.get("/api/graph-ml/dataset/status")
        assert ds_res.status_code == 200
        ds_data = ds_res.json()
        assert ds_data["total_transactions"] >= 5000
        assert ds_data["culprits_detected"] >= 10
        print(f"   [PASS] GET /api/graph-ml/dataset/status: {ds_data['total_transactions']} txs, {ds_data['culprits_detected']} culprits.")

        # Dataset Info (Elliptic++ specific)
        info_res = await client.get("/api/graph-ml/dataset/info")
        assert info_res.status_code == 200
        info_data = info_res.json()
        assert info_data["num_features"] >= 183
        assert info_data["timesteps"] == 49
        print(f"   [PASS] GET /api/graph-ml/dataset/info: {info_data['num_features']} features, {info_data['timesteps']} timesteps.")

        # Scored Transactions
        tx_scored_res = await client.get("/api/graph-ml/transactions/scored?limit=100")
        assert tx_scored_res.status_code == 200
        tx_list = tx_scored_res.json()
        assert len(tx_list) >= 100
        for tx in tx_list[:5]:
            assert "fraud_score" in tx
            assert "time_step" in tx
            assert "elliptic_class" in tx
        print(f"   [PASS] GET /api/graph-ml/transactions/scored returned {len(tx_list)} scored transactions.")

        # Identified Culprits with KYC
        culprits_res = await client.get("/api/graph-ml/culprits/identified")
        assert culprits_res.status_code == 200
        culprits_data = culprits_res.json()
        assert len(culprits_data) >= 10
        # Verify KYC records attached
        top = culprits_data[0]
        assert "kyc" in top
        assert top["kyc"]["resolution_status"] in ["IDENTIFIED", "IDENTIFIED_VIA_OFFRAMP", "UNHOSTED_UNVERIFIED"]
        print(f"   [PASS] GET /api/graph-ml/culprits/identified: {len(culprits_data)} culprits with KYC resolution.")

        # BNSS Dossier Generation
        dossier_payload = {
            "officerId": "IO-DELHI-402",
            "targetWallet": "tx_1",
            "terminalExchange": "Exchange Off-Ramp"
        }
        dossier_res = await client.post("/api/forensics/dossier/generate", json=dossier_payload)
        assert dossier_res.status_code == 200
        dossier_data = dossier_res.json()
        assert dossier_data["dossierId"].startswith("BNSS-94-")
        print(f"   [PASS] POST /api/forensics/dossier/generate created Dossier {dossier_data['dossierId']}.")

    print("\n" + "=" * 60)
    print("ALL BACKEND VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
