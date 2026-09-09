from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    tx_hash: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    network: Mapped[str] = mapped_column(String(20), default="TRC-20")
    from_address: Mapped[str] = mapped_column(String(100), ForeignKey("wallets.address"), index=True)
    to_address: Mapped[str] = mapped_column(String(100), ForeignKey("wallets.address"), index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    token: Mapped[str] = mapped_column(String(20), default="USDT")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    latency_seconds: Mapped[int] = mapped_column(Integer, default=0)
    gas_sponsor: Mapped[str] = mapped_column(String(100), nullable=True)