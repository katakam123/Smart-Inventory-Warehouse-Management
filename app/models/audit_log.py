
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Index
)
from sqlalchemy.sql import func

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)

    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)

    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
    )