"""
SIH 2026 — Wallet Model with WatchlistWallet Schema.

Extends the base Wallet SQLAlchemy model with a Pydantic schema for the
new "Watchlist Mode" (Proactive Alerting) feature. IOs can add known
mule wallets to a watchlist; if that wallet receives funds, the system
automatically triggers an alert.
"""

from sqlalchemy import String, Float, Integer, JSON, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.core.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    address: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    network: Mapped[str] = mapped_column(String(20), default="TRC-20")
    cluster_type: Mapped[str] = mapped_column(String(50), default="Unknown") # victim, mule, exchange, dust
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[int] = mapped_column(Integer, default=0) # 0 to 100
    heuristic_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)


# ==============================================================================
# SIH 2026 — Watchlist Mode (Proactive Mule Wallet Alerting)
# ==============================================================================

class WatchlistWallet(Base):
    """
    SIH 2026 — Watchlist Entry:
    Proactive alerting model. When an IO adds a known mule wallet to this
    watchlist, the system monitors all incoming transactions. If the watched
    wallet receives funds, an automatic alert is triggered for the IO.

    This transforms the system from purely reactive (trace after complaint)
    to proactive (alert on suspicious wallet activity).
    """
    __tablename__ = "watchlist_wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=True, default="Mule Wallet")
    added_by: Mapped[str] = mapped_column(String(100), nullable=False, default="IO-UNKNOWN")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reason: Mapped[str] = mapped_column(String(500), nullable=True, default=None)


class WatchlistAlert(Base):
    """
    SIH 2026 — Watchlist Alert Record:
    Generated when a watched wallet receives an incoming transaction.
    """
    __tablename__ = "watchlist_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    watchlist_wallet_address: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    triggered_tx_hash: Mapped[str] = mapped_column(String(100), nullable=True)
    from_address: Mapped[str] = mapped_column(String(100), nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[str] = mapped_column(String(100), nullable=True, default=None)


# ==============================================================================
# Pydantic Schemas for Watchlist API (SIH 2026)
# ==============================================================================

class WatchlistWalletSchema(BaseModel):
    """Pydantic schema for Watchlist Mode API requests/responses."""
    address: str = Field(..., description="Wallet address to monitor")
    label: Optional[str] = Field("Suspected Mule Wallet", description="Human-readable label")
    added_by: str = Field("IO-DELHI-402", description="Officer ID who added this entry")
    is_active: bool = Field(True, description="Whether monitoring is currently active")
    reason: Optional[str] = Field(None, description="Reason for adding to watchlist")

    class Config:
        from_attributes = True


class WatchlistAlertSchema(BaseModel):
    """Pydantic schema for Watchlist Alert responses."""
    id: int
    watchlist_wallet_address: str
    triggered_tx_hash: Optional[str] = None
    from_address: Optional[str] = None
    amount: float = 0.0
    triggered_at: Optional[datetime] = None
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None

    class Config:
        from_attributes = True