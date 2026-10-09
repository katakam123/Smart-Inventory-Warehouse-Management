from sqlalchemy import Boolean, Column, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    address = Column(String(500), nullable=True)
    credit_limit = Column(Numeric(12, 2), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    sales_orders = relationship("SalesOrder", back_populates="customer")