
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal


class TransferItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class TransferCreate(BaseModel):
    source_warehouse_id: int = Field(gt=0)
    destination_warehouse_id: int = Field(gt=0)
    items: list[TransferItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_warehouses(self):
        if self.source_warehouse_id == self.destination_warehouse_id:
            raise ValueError(
                "Source and destination warehouses must differ"
            )
        return self


class TransferReceiveItem(BaseModel):
    item_id: int = Field(gt=0)
    received_quantity: int = Field(ge=0)


class TransferReceive(BaseModel):
    items: list[TransferReceiveItem] = Field(min_length=1)


class TransferItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    requested_quantity: int
    dispatched_quantity: int | None
    received_quantity: int | None
    shortage_quantity: int
    notes: str | None


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_warehouse_id: int
    destination_warehouse_id: int
    status: str
    items: list[TransferItemResponse]