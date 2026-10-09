
from fastapi import APIRouter

router = APIRouter(tags=["Returns & Refunds"])


@router.get("/returns/health")
def returns_health():
    return {"message": "Returns router is working"}