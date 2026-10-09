from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)

    warehouse_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(
        String(150),
        nullable=False
    )

    city = Column(
        String(100),
        nullable=False
    )

    address = Column(
        String(500),
        nullable=False
    )

    capacity = Column(
        Integer,
        nullable=False
    )

    manager_id = Column(
        Integer,
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

    inventories = relationship(
        "Inventory",
        back_populates="warehouse"
    )