from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine, Base
from app.api import auth, forensics, graph_fraud
from app.engine.graph_model import graph_model_engine
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.vasp import VASPRegistry

async def seed_demo_blockchain_data():
    """Seeds the DB with initial testnet data matching the hackathon case scenario."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(VASPRegistry))
        if result.scalars().first() is None:
            # Seed Known VASP Registry
            vasp = VASPRegistry(
                exchange_name="CryptoGlobal Exchange (Hot Wallet 04)",
                hot_wallet_address="0xVASP_GlobalEx",
                network="TRC-20",
                jurisdiction="Seychelles / Non-Compliant",
                is_compliant=False
            )
            session.add(vasp)

            # Seed Wallets
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

            # Seed Transfer Transactions
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist in DB (fallback to local SQLite if Postgres is offline / auth fails)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_demo_blockchain_data()
    except Exception as db_err:
        print(f"PostgreSQL unavailable ({db_err}). Switching to local SQLite storage...")
        import os
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.pool import StaticPool
        sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chaintrace.db"))
        sqlite_url = f"sqlite+aiosqlite:///{sqlite_path}"
        fallback_engine = create_async_engine(sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        AsyncSessionLocal.configure(bind=fallback_engine)
        async with fallback_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_demo_blockchain_data()

    # Initialize Graph Machine Learning Fraud Detection Model with valid dataset
    try:
        graph_model_engine.load_dataset()
    except Exception as err:
        print(f"Graph model startup load warning: {err}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Automated Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges via Graph ML Analytics & KYC Intelligence (SIH 2026)",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for the React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(forensics.router, prefix=settings.API_V1_STR)
app.include_router(graph_fraud.router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "system": "ChainTrace Graph-ML Engine",
        "version": "2.0",
        "features": [
            "Graph Topological Feature Extraction (PageRank, HITS, In/Out Ratios)",
            "Every-Transaction Fraud Probability & Risk Scoring",
            "Automated Culprit Wallet Identification",
            "Culprit KYC & Off-Ramp Unmasking Intelligence",
            "BNSS Sec. 94 Digital Evidence Dossier Generator"
        ]
    }