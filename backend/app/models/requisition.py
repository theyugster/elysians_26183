"""
SIH 2026 — Requisition Model with Document Type Enum & Confidence Tracking.

Supports two document types:
  - BNSS_SEC_94_FREEZE: Standard freeze notice under BNSS Section 94
  - FIU_IND_ESCALATION: Escalation request to Financial Intelligence Unit India
    (used when exchange identity cannot be resolved)
"""

import enum
from sqlalchemy import String, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class DocumentType(str, enum.Enum):
    """
    SIH 2026 — Legal Document Type Enum:
    Defines the two types of legal instruments the system can generate.
    """
    BNSS_SEC_94_FREEZE = "BNSS_SEC_94_FREEZE"
    FIU_IND_ESCALATION = "FIU_IND_ESCALATION"


class RequisitionStatus(str, enum.Enum):
    """
    SIH 2026 — Requisition Lifecycle Status:
    DRAFT → REVIEWED → SIGNED → FINALIZED
    Ensures human-in-the-loop (HITL) compliance.
    """
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    SIGNED = "SIGNED"
    FINALIZED = "FINALIZED"
    REJECTED = "REJECTED"


class Requisition(Base):
    __tablename__ = "requisitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dossier_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    officer_id: Mapped[str] = mapped_column(String(100), nullable=False)
    target_wallet: Mapped[str] = mapped_column(String(100), nullable=False)
    terminal_exchange: Mapped[str] = mapped_column(String(120), nullable=False)
    sha256_audit_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # SIH 2026 — New fields for HITL compliance & confidence gating
    document_type: Mapped[str] = mapped_column(
        String(40),
        default=DocumentType.BNSS_SEC_94_FREEZE.value,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=RequisitionStatus.DRAFT.value,
        nullable=False
    )
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    confidence_tier: Mapped[str] = mapped_column(String(40), nullable=True, default=None)
    officer_signature_hash: Mapped[str] = mapped_column(String(64), nullable=True, default=None)