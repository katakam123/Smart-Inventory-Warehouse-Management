from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class WarehouseCreate(BaseModel):
    warehouse_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=255)
    capacity: int = Field(gt=0)
    manager_id: Optional[int] = None
    is_active: bool = True


class WarehouseUpdate(BaseModel):
    warehouse_code: Optional[str] = Field(
        default=None, min_length=1, max_length=50
    )
    name: Optional[str] = Field(
        default=None, min_length=1, max_length=100
    )
    city: Optional[str] = Field(
        default=None, min_length=1, max_length=100
    )
    address: Optional[str] = Field(
        default=None, min_length=1, max_length=255
    )
    capacity: Optional[int] = Field(default=None, gt=0)
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None


class WarehouseResponse(BaseModel):
    id: int
    warehouse_code: str
    name: str
    city: str
    address: str
    capacity: int
    manager_id: Optional[int]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)