from enum import Enum


class UserRole(str, Enum):
    ADMIN = "Admin"
    INVENTORY_MANAGER = "Inventory Manager"
    WAREHOUSE_STAFF = "Warehouse Staff"


class ProductUnit(str, Enum):
    PIECE = "Piece"
    BOX = "Box"
    KG = "Kg"
    LITRE = "Litre"


class StockMovementType(str, Enum):
    PURCHASE_RECEIPT = "Purchase Receipt"
    SALE_DISPATCH = "Sale Dispatch"
    CUSTOMER_RETURN = "Customer Return"
    TRANSFER_OUT = "Transfer Out"
    TRANSFER_IN = "Transfer In"
    ADJUSTMENT = "Adjustment"


class PurchaseOrderStatus(str, Enum):
    DRAFT = "Draft"
    APPROVED = "Approved"
    PARTIALLY_RECEIVED = "Partially Received"
    RECEIVED = "Received"
    CANCELLED = "Cancelled"


class SalesOrderStatus(str, Enum):
    DRAFT = "Draft"
    CONFIRMED = "Confirmed"
    PICKED = "Picked"
    PACKED = "Packed"
    DISPATCHED = "Dispatched"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


class ReturnStatus(str, Enum):
    REQUESTED = "Requested"
    INSPECTED = "Inspected"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    REFUNDED = "Refunded"


class ReturnCondition(str, Enum):
    GOOD = "Good"
    DAMAGED = "Damaged"