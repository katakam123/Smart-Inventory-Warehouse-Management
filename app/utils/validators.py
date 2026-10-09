
import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session


PHONE_PATTERN = re.compile(r"^[6-9]\d{9}$")

# Standard Indian GSTIN structure:
# 2-digit state code + 10-character PAN +
# entity digit + Z + checksum character.
GST_PATTERN = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"
)


def validate_phone(phone: str) -> str:
    phone = phone.strip()

    if not PHONE_PATTERN.fullmatch(phone):
        raise ValueError(
            "Phone number must be a valid 10-digit Indian mobile number"
        )

    return phone


def validate_gst(gst_number: str) -> str:
    gst_number = gst_number.strip().upper()

    if not GST_PATTERN.fullmatch(gst_number):
        raise ValueError("Invalid GSTIN format")

    return gst_number


def ensure_unique(
    db: Session,
    model,
    field_name: str,
    value,
    exclude_id: int | None = None,
):
    """Raise HTTP 409 if a value already exists in the database."""

    column = getattr(model, field_name, None)

    if column is None:
        raise ValueError(
            f"Unknown field '{field_name}' on {model.__name__}"
        )

    statement = select(model).where(column == value)

    if exclude_id is not None and hasattr(model, "id"):
        statement = statement.where(model.id != exclude_id)

    existing_record = db.scalar(statement)

    if existing_record:
        raise HTTPException(
            status_code=409,
            detail=f"{field_name} '{value}' already exists",
        )