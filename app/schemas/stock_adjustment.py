
from typing import Literal
from pydantic import BaseModel, Field


class AdjustmentCreate(BaseModel):
    warehouse_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    adjustment_type: Literal["Increase", "Decrease"]
    reason: Literal[
        "Damaged",
        "Lost",
        "Expired",
        "Found",
        "Count Correction",
    ]
    quantity: int = Field(gt=0)
    request_notes: str | None = None


class AdjustmentReview(BaseModel):
    review_notes: str | None = None