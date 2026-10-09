from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):

    name: str
    sku: str
    barcode: str | None = None
    category_id: int
    unit: str

    cost_price: Decimal = Field(gt=0)
    selling_price: Decimal = Field(gt=0)

    reorder_level: int = Field(ge=0)
    reorder_quantity: int = Field(gt=0)

    preferred_supplier_id: int | None = None


class ProductUpdate(BaseModel):

    name: str | None = None
    barcode: str | None = None
    category_id: int | None = None
    unit: str | None = None

    cost_price: Decimal | None = Field(
        default=None,
        gt=0
    )

    selling_price: Decimal | None = Field(
        default=None,
        gt=0
    )

    reorder_level: int | None = Field(
        default=None,
        ge=0
    )

    reorder_quantity: int | None = Field(
        default=None,
        gt=0
    )

    preferred_supplier_id: int | None = None


class ProductResponse(BaseModel):

    id: int
    name: str
    sku: str
    barcode: str | None
    category_id: int
    unit: str
    cost_price: Decimal
    selling_price: Decimal
    reorder_level: int
    reorder_quantity: int
    preferred_supplier_id: int | None
    is_active: bool

    class Config:
        from_attributes = True