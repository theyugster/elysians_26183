from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class VASPRegistry(Base):
    __tablename__ = "vasp_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exchange_name: Mapped[str] = mapped_column(String(120), nullable=False)
    hot_wallet_address: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    network: Mapped[str] = mapped_column(String(20), default="TRC-20")
    jurisdiction: Mapped[str] = mapped_column(String(100), default="Unknown / Offshore")
    is_compliant: Mapped[bool] = mapped_column(default=False)