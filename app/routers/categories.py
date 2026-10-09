from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.permissions import require_roles
from app.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)


router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_roles(
        current_user,
        ["Admin", "Inventory Manager"]
    )

    existing = db.query(Category).filter(
        Category.category_name == data.category_name
    ).first()

    if existing:

        raise HTTPException(
            status_code=409,
            detail="Category already exists"
        )

    category = Category(
        category_name=data.category_name,
        description=data.description,
        created_by=current_user.id
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.get(
    "",
    response_model=list[CategoryResponse]
)
def get_categories(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return (
        db.query(Category)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.put(
    "/{category_id}",
    response_model=CategoryResponse
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_roles(
        current_user,
        ["Admin", "Inventory Manager"]
    )

    category = db.query(Category).filter(
        Category.id == category_id
    ).first()

    if not category:

        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    if data.category_name is not None:
        category.category_name = data.category_name

    if data.description is not None:
        category.description = data.description

    db.commit()
    db.refresh(category)

    return category


@router.delete(
    "/{category_id}"
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_roles(
        current_user,
        ["Admin", "Inventory Manager"]
    )

    category = db.query(Category).filter(
        Category.id == category_id
    ).first()

    if not category:

        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    active_product = db.query(Product).filter(
        Product.category_id == category_id,
        Product.is_active == True
    ).first()

    if active_product:

        raise HTTPException(
            status_code=400,
            detail="Category has active products"
        )

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted successfully"
    }