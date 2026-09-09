from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class HeuristicsBreakdown(BaseModel):
    vaspMatch: int
    sweeper: int
    gasSponsor: int
    fanIn: int

class NodeSchema(BaseModel):
    id: str
    label: str
    type: str
    riskScore: int
    balance: str
    cluster: str
    exchangeName: Optional[str] = None
    jurisdiction: Optional[str] = None
    heuristics: HeuristicsBreakdown

class LinkSchema(BaseModel):
    source: str
    target: str
    amount: str
    txHash: str
    suspiciousScore: int
    latency: str

class ForensicTraceResponse(BaseModel):
    target: str
    terminalExchange: Optional[str]
    traversalTimeMs: float
    nodesCount: int
    prunedDustBranches: int
    nodes: List[NodeSchema]
    links: List[LinkSchema]

class RequisitionCreate(BaseModel):
    officerId: str
    targetWallet: str
    terminalExchange: str

class RequisitionResponse(BaseModel):
    dossierId: str
    officerId: str
    targetWallet: str
    terminalExchange: str
    sha256AuditHash: str
    createdAt: datetime
    legalMandate: str

class SystemStatsResponse(BaseModel):
    totalTrackedVolume: str
    identifiedVaspsCount: int
    totalTransactionsCount: int
    highRiskWalletsCount: int

class VASPRegistryItem(BaseModel):
    id: int
    exchangeName: str
    hotWalletAddress: str
    network: str
    jurisdiction: str
    isCompliant: bool

class WalletProfileResponse(BaseModel):
    address: str
    network: str
    clusterType: str
    balance: float
    riskScore: int
    heuristics: Optional[HeuristicsBreakdown] = None