import os
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status
from app.engine.graph_model import graph_model_engine
from app.engine.kyc_resolver import kyc_resolver_engine
from app.schemas.graph_fraud import (
    TransactionScoredResponse,
    CulpritProfileResponse,
    KYCResolutionResponse,
    GraphDatasetStatusResponse,
    GraphAnalysisResponse,
    LoadDatasetPayload,
    DatasetInfoResponse
)

router = APIRouter(prefix="/graph-ml", tags=["Graph ML Fraud & KYC Engine"])

@router.post("/dataset/load", response_model=GraphDatasetStatusResponse)
async def load_transaction_dataset(payload: Optional[LoadDatasetPayload] = None):
    """
    Loads the Elliptic++ blockchain transaction dataset into the Graph Fraud ML Engine,
    trains Random Forest on labeled data, extracts topological features, and scores all transactions.
    """
    custom_path = payload.dataset_path if payload else None
    try:
        summary = graph_model_engine.load_dataset(custom_path=custom_path)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to load dataset: {str(e)}"
        )

@router.get("/dataset/status", response_model=GraphDatasetStatusResponse)
async def get_dataset_status():
    """Returns current status and metrics of the loaded Elliptic++ graph dataset."""
    if not graph_model_engine.is_loaded:
        graph_model_engine.load_dataset()

    return {
        "status": "ACTIVE",
        "total_transactions": len(graph_model_engine.scored_transactions),
        "unique_wallets": graph_model_engine.dataset_info.get("unique_wallets", 0),
        "graph_edges": graph_model_engine.g.number_of_edges(),
        "culprits_detected": len(graph_model_engine.culprits),
        "dataset_file": "Elliptic++ (5,000 txs, 183 features, Random Forest)"
    }

@router.get("/dataset/info", response_model=DatasetInfoResponse)
async def get_dataset_info():
    """Returns detailed Elliptic++ dataset statistics including class distribution and model metrics."""
    if not graph_model_engine.is_loaded:
        graph_model_engine.load_dataset()

    return graph_model_engine.get_dataset_info()

@router.get("/analyze", response_model=GraphAnalysisResponse)
async def analyze_graph(
    target: str = Query(default="tx_1", description="Target transaction ID (e.g. tx_1) or wallet address"),
    hops: int = Query(default=3, ge=1, le=10, description="Max BFS propagation hops")
):
    """
    Runs Graph ML inference starting from target wallet or transaction.
    Returns nodes and edges scored by the Random Forest + graph-topological model.
    """
    if not graph_model_engine.is_loaded:
        graph_model_engine.load_dataset()

    subgraph = graph_model_engine.get_scored_subgraph(root_target=target, max_hops=hops)
    return subgraph

@router.get("/transactions/scored", response_model=List[TransactionScoredResponse])
async def list_scored_transactions(
    min_score: int = Query(default=0, ge=0, le=100, description="Minimum fraud score filter"),
    classification: Optional[str] = Query(default=None, description="FRAUDULENT, SUSPICIOUS, or LEGITIMATE"),
    limit: int = Query(default=500, ge=1, le=5000, description="Max transactions to return")
):
    """
    Returns all dataset transactions evaluated and scored against the Graph Model,
    complete with probability, calibrated fraud score, and risk factors.
    """
    if not graph_model_engine.is_loaded:
        graph_model_engine.load_dataset()

    txs = graph_model_engine.scored_transactions
    if min_score > 0:
        txs = [t for t in txs if t["fraud_score"] >= min_score]
    if classification:
        txs = [t for t in txs if t["classification"].upper() == classification.upper()]

    return txs[:limit]

@router.get("/culprits/identified", response_model=List[CulpritProfileResponse])
async def get_identified_culprits():
    """
    Returns all culprit wallets identified by the Graph Model along with
    their resolved KYC intelligence (direct match or downstream cash-out unmasking).
    """
    if not graph_model_engine.is_loaded:
        graph_model_engine.load_dataset()

    culprits = graph_model_engine.culprits
    resolved_culprits = kyc_resolver_engine.resolve_all_culprits(
        culprits=culprits,
        graph=graph_model_engine.g
    )
    return resolved_culprits

@router.get("/wallet/{address}/kyc", response_model=KYCResolutionResponse)
async def resolve_wallet_kyc(address: str):
    """
    Resolves KYC profile for a specific wallet address.
    If the wallet is an unhosted mule, traces downstream graph paths to unmask the cash-out recipient.
    """
    if not graph_model_engine.is_loaded:
        graph_model_engine.load_dataset()

    kyc_profile = kyc_resolver_engine.resolve_wallet_kyc(
        wallet_address=address,
        graph=graph_model_engine.g
    )
    return kyc_profile
