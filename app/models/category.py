from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)

    category_name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    description = Column(
        String(500),
        nullable=True
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

    products = relationship(
        "Product",
        back_populates="category"
    )