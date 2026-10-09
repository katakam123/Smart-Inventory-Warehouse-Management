from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    gst_number = Column(String(30), unique=True, nullable=True)
    address = Column(Text, nullable=True)
    lead_time_days = Column(Integer, nullable=False, default=7)
    is_active = Column(Boolean, nullable=False, default=True)

    purchase_orders = relationship(
        "PurchaseOrder",
        back_populates="supplier",
    )