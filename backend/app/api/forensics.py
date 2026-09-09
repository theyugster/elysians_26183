import hashlib
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.engine.traversal import run_5hop_bfs_traversal
from app.schemas.forensics import (
    ForensicTraceResponse, 
    RequisitionCreate, 
    RequisitionResponse,
    SystemStatsResponse,
    VASPRegistryItem,
    WalletProfileResponse
)
from app.models.requisition import Requisition
from app.models.vasp import VASPRegistry
from app.models.wallet import Wallet
from app.models.transaction import Transaction

router = APIRouter(prefix="/forensics", tags=["Forensics Engine"])

@router.get("/trace", response_model=ForensicTraceResponse)
async def trace_target(
    target: str = Query(default="0xVic_9011", description="Victim Wallet Address or Tx Hash"),
    db: AsyncSession = Depends(get_db)
):
    nodes, links, terminal_exchange, pruned_count, exec_time = await run_5hop_bfs_traversal(
        db=db, 
        root_target=target
    )
    return {
        "target": target,
        "terminalExchange": terminal_exchange or "CryptoGlobal Exchange (Hot Wallet 04)",
        "traversalTimeMs": exec_time,
        "nodesCount": len(nodes),
        "prunedDustBranches": pruned_count,
        "nodes": nodes,
        "links": links
    }

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    # Calculate overall dashboard metrics
    vol_res = await db.execute(select(func.sum(Transaction.amount)))
    total_vol = vol_res.scalar() or 0.0

    vasp_res = await db.execute(select(func.count(VASPRegistry.id)))
    vasp_count = vasp_res.scalar() or 0

    tx_res = await db.execute(select(func.count(Transaction.tx_hash)))
    tx_count = tx_res.scalar() or 0

    high_risk_res = await db.execute(select(func.count(Wallet.address)).where(Wallet.risk_score >= 70))
    high_risk_count = high_risk_res.scalar() or 0

    return {
        "totalTrackedVolume": f"${total_vol:,.2f} USDT",
        "identifiedVaspsCount": vasp_count,
        "totalTransactionsCount": tx_count,
        "highRiskWalletsCount": high_risk_count
    }

@router.get("/vasp-registry", response_model=List[VASPRegistryItem])
async def list_vasp_registry(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VASPRegistry))
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "exchangeName": r.exchange_name,
            "hotWalletAddress": r.hot_wallet_address,
            "network": r.network,
            "jurisdiction": r.jurisdiction,
            "isCompliant": r.is_compliant
        }
        for r in records
    ]

@router.get("/wallet/{address}", response_model=WalletProfileResponse)
async def get_wallet_profile(address: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Wallet).where(Wallet.address == address))
    wallet = res.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet address not found")
    
    breakdown = wallet.heuristic_breakdown or {
        "vaspMatch": 90 if wallet.cluster_type == "exchange" else 10,
        "sweeper": 75 if wallet.cluster_type == "mule" else 5,
        "gasSponsor": 45,
        "fanIn": 80 if wallet.cluster_type == "mule" else 15
    }

    return {
        "address": wallet.address,
        "network": wallet.network,
        "clusterType": wallet.cluster_type,
        "balance": wallet.balance,
        "riskScore": wallet.risk_score,
        "heuristics": breakdown
    }

@router.post("/dossier/generate", response_model=RequisitionResponse)
async def generate_bnss_requisition(
    payload: RequisitionCreate,
    db: AsyncSession = Depends(get_db)
):
    timestamp = datetime.utcnow().isoformat()
    raw_signature = f"{payload.officerId}:{payload.targetWallet}:{payload.terminalExchange}:{timestamp}"
    audit_hash = hashlib.sha256(raw_signature.encode()).hexdigest()
    dossier_id = f"BNSS-94-{audit_hash[:10].upper()}"

    requisition_record = Requisition(
        dossier_id=dossier_id,
        officer_id=payload.officerId,
        target_wallet=payload.targetWallet,
        terminal_exchange=payload.terminalExchange,
        sha256_audit_hash=audit_hash
    )
    db.add(requisition_record)
    await db.commit()
    await db.refresh(requisition_record)

    return {
        "dossierId": requisition_record.dossier_id,
        "officerId": requisition_record.officer_id,
        "targetWallet": requisition_record.target_wallet,
        "terminalExchange": requisition_record.terminal_exchange,
        "sha256AuditHash": requisition_record.sha256_audit_hash,
        "createdAt": requisition_record.created_at,
        "legalMandate": "Bharatiya Nagarik Suraksha Sanhita (BNSS) Section 94 Digital Evidence Order"
    }

@router.get("/dossiers", response_model=List[RequisitionResponse])
async def list_requisition_dossiers(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Requisition).order_by(Requisition.created_at.desc()))
    records = res.scalars().all()
    return [
        {
            "dossierId": r.dossier_id,
            "officerId": r.officer_id,
            "targetWallet": r.target_wallet,
            "terminalExchange": r.terminal_exchange,
            "sha256AuditHash": r.sha256_audit_hash,
            "createdAt": r.created_at,
            "legalMandate": "Bharatiya Nagarik Suraksha Sanhita (BNSS) Section 94 Digital Evidence Order"
        }
        for r in records
    ]