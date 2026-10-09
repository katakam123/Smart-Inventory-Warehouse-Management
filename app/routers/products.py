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
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_roles(
        current_user,
        ["Admin", "Inventory Manager"]
    )

    if data.selling_price < data.cost_price:

        raise HTTPException(
            status_code=422,
            detail="Selling price must be greater than or equal to cost price"
        )

    category = db.query(Category).filter(
        Category.id == data.category_id
    ).first()

    if not category:

        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    existing_sku = db.query(Product).filter(
        Product.sku == data.sku
    ).first()

    if existing_sku:

        raise HTTPException(
            status_code=409,
            detail="SKU already exists"
        )

    if data.barcode:

        existing_barcode = db.query(Product).filter(
            Product.barcode == data.barcode
        ).first()

        if existing_barcode:

            raise HTTPException(
                status_code=409,
                detail="Barcode already exists"
            )

    product = Product(
        name=data.name,
        sku=data.sku,
        barcode=data.barcode,
        category_id=data.category_id,
        unit=data.unit,
        cost_price=data.cost_price,
        selling_price=data.selling_price,
        reorder_level=data.reorder_level,
        reorder_quantity=data.reorder_quantity,
        preferred_supplier_id=data.preferred_supplier_id,
        created_by=current_user.id
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get(
    "",
    response_model=list[ProductResponse]
)
def get_products(
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    query = db.query(Product)

    if search:

        query = query.filter(
            Product.name.contains(search)
            | Product.sku.contains(search)
        )

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/{product_id}"
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    inventories = db.query(Inventory).filter(
        Inventory.product_id == product_id
    ).all()

    stock_by_warehouse = []

    total_stock = 0

    for inventory in inventories:

        total_stock += inventory.quantity_on_hand

        stock_by_warehouse.append(
            {
                "warehouse_id": inventory.warehouse_id,
                "quantity_on_hand": inventory.quantity_on_hand,
                "quantity_reserved": inventory.quantity_reserved,
                "quantity_available": (
                    inventory.quantity_on_hand
                    - inventory.quantity_reserved
                )
            }
        )

    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "barcode": product.barcode,
        "category_id": product.category_id,
        "unit": product.unit,
        "cost_price": product.cost_price,
        "selling_price": product.selling_price,
        "reorder_level": product.reorder_level,
        "reorder_quantity": product.reorder_quantity,
        "preferred_supplier_id": product.preferred_supplier_id,
        "is_active": product.is_active,
        "total_stock": total_stock,
        "stock_by_warehouse": stock_by_warehouse
    }


@router.put(
    "/{product_id}",
    response_model=ProductResponse
)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_roles(
        current_user,
        ["Admin", "Inventory Manager"]
    )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    new_cost = update_data.get(
        "cost_price",
        product.cost_price
    )

    new_selling = update_data.get(
        "selling_price",
        product.selling_price
    )

    if new_selling < new_cost:

        raise HTTPException(
            status_code=422,
            detail="Selling price must be greater than or equal to cost price"
        )

    for field, value in update_data.items():

        setattr(
            product,
            field,
            value
        )

    db.commit()
    db.refresh(product)

    return product


@router.delete(
    "/{product_id}"
)
def deactivate_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_roles(
        current_user,
        ["Admin", "Inventory Manager"]
    )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    inventory = db.query(Inventory).filter(
        Inventory.product_id == product_id,
        Inventory.quantity_on_hand > 0
    ).first()

    if inventory:

        raise HTTPException(
            status_code=400,
            detail="Product with stock cannot be deactivated"
        )

    product.is_active = False

    db.commit()

    return {
        "message": "Product deactivated successfully"
    }