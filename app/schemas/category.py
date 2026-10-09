from pydantic import BaseModel


class CategoryCreate(BaseModel):

    category_name: str
    description: str | None = None


class CategoryUpdate(BaseModel):

    category_name: str | None = None
    description: str | None = None


class CategoryResponse(BaseModel):

    id: int
    category_name: str
    description: str | None

    class Config:
        from_attributes = True