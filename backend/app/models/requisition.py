from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base

class Requisition(Base):
    __tablename__ = "requisitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dossier_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    officer_id: Mapped[str] = mapped_column(String(100), nullable=False)
    target_wallet: Mapped[str] = mapped_column(String(100), nullable=False)
    terminal_exchange: Mapped[str] = mapped_column(String(120), nullable=False)
    sha256_audit_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)