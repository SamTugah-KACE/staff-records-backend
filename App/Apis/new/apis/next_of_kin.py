from uuid import UUID
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.new.schemas import next_of_kin as schemas
from Apis.new.services.next_of_kin import next_of_kin_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

next_of_kin_router = APIRouter(prefix="/next_of_kins")


@next_of_kin_router.get(
    "",
    response_model=List[schemas.NextOfKinSchema],
)
async def list_next_of_kins(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        employee_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
) -> Any:
    next_of_kins = await actions.list_next_of_kins(
        db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
    )
    return next_of_kins


@next_of_kin_router.post(
    "",
    response_model=schemas.NextOfKinSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_next_of_kin(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.NextOfKinCreate
) -> Any:
    next_of_kin = await actions.create_next_of_kin(db=db, data=data)
    return next_of_kin


@next_of_kin_router.put(
    "/{id}",
    response_model=schemas.NextOfKinSchema,
)
async def update_next_of_kin(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.NextOfKinUpdate,
) -> Any:
    next_of_kin = await actions.update_next_of_kin(db=db, id=id, data=data)
    return next_of_kin


@next_of_kin_router.get(
    "/{id}",
    response_model=schemas.NextOfKinSchema,
)
async def get_next_of_kin(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    next_of_kin = await actions.get_next_of_kin(db=db, id=id)
    return next_of_kin


@next_of_kin_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_next_of_kin(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_next_of_kin(db=db, id=id)
