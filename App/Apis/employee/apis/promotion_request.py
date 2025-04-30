from uuid import UUID
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.employee.schemas import promotion_request as schemas
from Apis.employee.services.promotion_request import promotion_request_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

promotion_request_router = APIRouter(prefix="/promotion_requests")


@promotion_request_router.get(
    "",
    response_model=List[schemas.PromotionRequestSchema],
)
async def list_promotion_requests(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        employee_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
) -> Any:
    promotion_requests = await actions.list_promotion_requests(
        db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
    )
    return promotion_requests


@promotion_request_router.post(
    "",
    response_model=schemas.PromotionRequestSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_promotion_request(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.PromotionRequestCreate
) -> Any:
    promotion_request = await actions.create_promotion_request(db=db, data=data)
    return promotion_request


@promotion_request_router.put(
    "/{id}",
    response_model=schemas.PromotionRequestSchema,
)
async def update_promotion_request(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.PromotionRequestUpdate,
) -> Any:
    promotion_request = await actions.update_promotion_request(db=db, id=id, data=data)
    return promotion_request


@promotion_request_router.get(
    "/{id}",
    response_model=schemas.PromotionRequestSchema,
)
async def get_promotion_request(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    promotion_request = await actions.get_promotion_request(db=db, id=id)
    return promotion_request


@promotion_request_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_promotion_request(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_promotion_request(db=db, id=id)
