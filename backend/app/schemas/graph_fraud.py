from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class KYCBankAccount(BaseModel):
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    swift_bic: Optional[str] = None
    ifsc: Optional[str] = None
    currency: Optional[str] = "USD"

class KYCIdentitySchema(BaseModel):
    entity_name: Optional[str] = None
    primary_beneficiary: Optional[str] = None
    national_id: Optional[str] = None
    tax_id: Optional[str] = None
    jurisdiction: Optional[str] = None
    physical_address: Optional[str] = None
    registered_email: Optional[str] = None
    registered_phone: Optional[str] = None
    associated_ips: List[str] = []
    linked_bank_accounts: List[Dict[str, Any]] = []

class KYCResolutionResponse(BaseModel):
    wallet_address: str
    resolution_status: str
    match_type: str
    identity: KYCIdentitySchema
    kyc_tier: str
    risk_classification: str
    legal_readiness: str
    traced_cashout_wallet: Optional[str] = None
    hops_to_cashout: Optional[int] = None
    flow_path: Optional[List[str]] = None
    downstream_trace: Optional[Dict[str, Any]] = None

class CulpritProfileResponse(BaseModel):
    address: str
    threat_score: int
    role: str
    is_culprit: bool
    in_degree: int
    out_degree: int
    pagerank: float
    in_volume: float
    out_volume: float
    kyc: KYCResolutionResponse

class TransactionScoredResponse(BaseModel):
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    formatted_amount: str
    latency_seconds: int
    gas_sponsor: Optional[str] = None
    tx_type: str
    fraud_probability: float
    fraud_score: int
    classification: str
    risk_factors: List[str]
    timestamp: Optional[str] = None
    time_step: Optional[int] = None
    elliptic_class: Optional[int] = None

class GraphDatasetStatusResponse(BaseModel):
    status: str
    total_transactions: int
    unique_wallets: int
    graph_edges: int
    culprits_detected: int
    dataset_file: str

class DatasetInfoResponse(BaseModel):
    total_transactions: int
    total_edges: int
    unique_wallets: int
    num_features: int
    timesteps: int
    class_distribution: Dict[str, int]
    graph_nodes: int
    graph_edges: int
    model_training_time_ms: float

class LoadDatasetPayload(BaseModel):
    dataset_path: Optional[str] = None

class GraphAnalysisResponse(BaseModel):
    target: str
    terminalExchange: Optional[str] = None
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    culprits_detected: List[Dict[str, Any]]
    total_nodes: int
    total_links: int
