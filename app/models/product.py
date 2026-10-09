from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(200),
        nullable=False,
        index=True
    )

    sku = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    barcode = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False
    )

    unit = Column(
        String(30),
        nullable=False
    )

    cost_price = Column(
        Numeric(12, 2),
        nullable=False
    )

    selling_price = Column(
        Numeric(12, 2),
        nullable=False
    )

    reorder_level = Column(
        Integer,
        nullable=False,
        default=0
    )

    reorder_quantity = Column(
        Integer,
        nullable=False,
        default=0
    )

    preferred_supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    created_by = Column(
        Integer,
        nullable=True
    )

    category = relationship(
        "Category",
        back_populates="products"
    )

    inventories = relationship(
        "Inventory",
        back_populates="product"
    )

    stock_movements = relationship(
        "StockMovement",
        back_populates="product"
    )