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
from app.engine.heuristics import (
    calculate_sweeper_score,
    calculate_gas_sponsor_score,
    calculate_fan_in_score,
    compute_node_threat_score
)
from app.engine.traversal import run_5hop_bfs_traversal

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

    # 1. Test Heuristics
    print("\n1. Testing Multi-Signal Heuristic Matrix...")
    # Sweeper score
    sw1 = calculate_sweeper_score(latency_seconds=15, forwarded_ratio=0.98)
    assert sw1 == 100, f"Expected 100, got {sw1}"
    sw2 = calculate_sweeper_score(latency_seconds=120, forwarded_ratio=0.5)
    assert sw2 == 15, f"Expected 15, got {sw2}"
    print("   [PASS] Sweeper scoring heuristics verified.")

    # Gas sponsor score
    g0 = calculate_gas_sponsor_score(has_external_sponsor=False, sponsor_shared_count=0)
    assert g0 == 0, f"Expected 0, got {g0}"
    g_high = calculate_gas_sponsor_score(has_external_sponsor=True, sponsor_shared_count=4)
    assert g_high == 95, f"Expected 95, got {g_high}"
    print("   [PASS] Gas sponsor profiling heuristics verified.")

    # Fan-in score
    f_high = calculate_fan_in_score(in_degree=4, out_degree=1)
    assert f_high == 96, f"Expected 96, got {f_high}"
    f_mid = calculate_fan_in_score(in_degree=2, out_degree=3)
    assert f_mid == 65, f"Expected 65, got {f_mid}"
    print("   [PASS] Fan-In topology heuristics verified.")

    # Threat score
    t_vasp = compute_node_threat_score(vasp=100, sweeper=50, gas=0, fan_in=65, is_vasp=True)
    assert t_vasp >= 90, f"Expected >= 90 for VASP, got {t_vasp}"
    print("   [PASS] Composite threat index computation verified.")

    # 2. Setup In-Memory Database & Seed
    print("\n2. Initializing SQLite In-Memory Database and Tables...")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed data using TestSessionLocal
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
            Wallet(address="0xMule_A2", cluster_type="mule", balance=14200.00, risk_score=74),
            Wallet(address="0xMule_B1", cluster_type="mule", balance=23100.00, risk_score=82),
            Wallet(address="0xConsol_99", cluster_type="mule", balance=94800.00, risk_score=92),
            Wallet(address="0xVASP_GlobalEx", cluster_type="exchange", balance=1420000.00, risk_score=97),
            Wallet(address="0xDust_Pruned", cluster_type="dust", balance=42.00, risk_score=35),
        ]
        session.add_all(wallets)
        await session.flush()

        txs = [
            Transaction(tx_hash="0x71fb_a301", from_address="0xVic_9011", to_address="0xMule_A1", amount=48500.0, latency_seconds=42, gas_sponsor="0xGasSponsor_Sybil"),
            Transaction(tx_hash="0x88ea_120f", from_address="0xMule_A1", to_address="0xMule_A2", amount=24000.0, latency_seconds=18, gas_sponsor="0xGasSponsor_Sybil"),
            Transaction(tx_hash="0x99cb_e843", from_address="0xMule_A1", to_address="0xMule_B1", amount=23800.0, latency_seconds=22, gas_sponsor="0xGasSponsor_Sybil"),
            Transaction(tx_hash="0x22ab_9900", from_address="0xVic_9011", to_address="0xDust_Pruned", amount=700.0, latency_seconds=120),
            Transaction(tx_hash="0x33dc_91bc", from_address="0xMule_A2", to_address="0xConsol_99", amount=23950.0, latency_seconds=12),
            Transaction(tx_hash="0x44fa_7302", from_address="0xMule_B1", to_address="0xConsol_99", amount=23720.0, latency_seconds=15),
            Transaction(tx_hash="0x10fe_ca41", from_address="0xConsol_99", to_address="0xVASP_GlobalEx", amount=47500.0, latency_seconds=8),
        ]
        session.add_all(txs)
        await session.commit()
    print("   [PASS] Demo blockchain data seeded.")

    # 3. Direct Traversal Test
    print("\n3. Testing 5-Hop BFS Traversal with Dust Pruning (<3%)...")
    async with TestSessionLocal() as session:
        nodes, links, terminal_exchange, pruned_count, exec_time = await run_5hop_bfs_traversal(session, "0xVic_9011")
        print(f"   Nodes found: {len(nodes)}")
        print(f"   Links found: {len(links)}")
        print(f"   Terminal exchange: {terminal_exchange}")
        print(f"   Pruned dust branches: {pruned_count}")
        print(f"   Traversal latency: {exec_time} ms")

        assert terminal_exchange == "CryptoGlobal Exchange (Hot Wallet 04)", f"Wrong terminal exchange: {terminal_exchange}"
        assert pruned_count == 1, f"Expected 1 pruned dust branch, got {pruned_count}"
        assert any(n["id"] == "0xVASP_GlobalEx" for n in nodes), "0xVASP_GlobalEx missing from nodes"
        assert not any(n["id"] == "0xDust_Pruned" for n in nodes), "0xDust_Pruned should have been pruned!"
        print("   [PASS] 5-Hop BFS Traversal successfully identified off-ramp and pruned dust.")

    # 4. HTTP API Endpoints Test
    print("\n4. Testing FastAPI HTTP Endpoints via AsyncClient...")
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
        token = auth_res.json()["access_token"]
        assert token.startswith("bearer_token_signed_for_IO-DELHI-402")
        print("   [PASS] POST /api/auth/login authorized officer credentials.")

        # Auth Login - reject invalid
        auth_invalid = await client.post("/api/auth/login", json={"officerId": "HACKER-007", "pin": "0000"})
        assert auth_invalid.status_code == 401
        print("   [PASS] POST /api/auth/login rejected unauthorized officer ID.")

        # Forensics Trace
        trace_res = await client.get("/api/forensics/trace?target=0xVic_9011")
        assert trace_res.status_code == 200, f"Trace failed: {trace_res.text}"
        trace_data = trace_res.json()
        assert trace_data["terminalExchange"] == "CryptoGlobal Exchange (Hot Wallet 04)"
        assert trace_data["prunedDustBranches"] == 1
        assert len(trace_data["nodes"]) >= 6
        assert len(trace_data["links"]) >= 6
        print("   [PASS] GET /api/forensics/trace returned valid ForensicTraceResponse.")

        # BNSS Dossier Generation
        dossier_payload = {
            "officerId": "IO-DELHI-402",
            "targetWallet": "0xVic_9011",
            "terminalExchange": "CryptoGlobal Exchange (Hot Wallet 04)"
        }
        dossier_res = await client.post("/api/forensics/dossier/generate", json=dossier_payload)
        assert dossier_res.status_code == 200, f"Dossier generation failed: {dossier_res.text}"
        dossier_data = dossier_res.json()
        assert dossier_data["dossierId"].startswith("BNSS-94-")
        assert len(dossier_data["sha256AuditHash"]) == 64
        assert "BNSS" in dossier_data["legalMandate"]
        print(f"   [PASS] POST /api/forensics/dossier/generate created Dossier {dossier_data['dossierId']}.")

        # Forensics Stats
        stats_res = await client.get("/api/forensics/stats")
        assert stats_res.status_code == 200
        stats_data = stats_res.json()
        assert stats_data["identifiedVaspsCount"] == 1
        print("   [PASS] GET /api/forensics/stats returned metrics.")

        # VASP Registry
        vasp_res = await client.get("/api/forensics/vasp-registry")
        assert vasp_res.status_code == 200
        assert len(vasp_res.json()) == 1
        print("   [PASS] GET /api/forensics/vasp-registry listed registered VASPs.")

        # Wallet Profile
        w_res = await client.get("/api/forensics/wallet/0xMule_A1")
        assert w_res.status_code == 200
        w_data = w_res.json()
        assert w_data["clusterType"] == "mule"
        print("   [PASS] GET /api/forensics/wallet/{address} returned wallet profile.")

        # Dossier List
        d_res = await client.get("/api/forensics/dossiers")
        assert d_res.status_code == 200
        assert len(d_res.json()) >= 1
        print("   [PASS] GET /api/forensics/dossiers listed saved dossiers.")

    print("\nALL 8/8 BACKEND VERIFICATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_tests())
