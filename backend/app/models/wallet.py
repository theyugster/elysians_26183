from sqlalchemy import String, Float, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    address: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    network: Mapped[str] = mapped_column(String(20), default="TRC-20")
    cluster_type: Mapped[str] = mapped_column(String(50), default="Unknown") # victim, mule, exchange, dust
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[int] = mapped_column(Integer, default=0) # 0 to 100
    heuristic_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)