from fastapi import APIRouter, Depends

from app.repositories.dependencies import get_uow
from app.repositories.unit_of_work import UnitOfWork
from app.services.order_service import create_order


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

@router.post("/")
async def create_order_endpoint(
        uow: UnitOfWork = Depends(
            get_uow,
            scope="function"
        )
):
    return await create_order(
        uow=uow
    )