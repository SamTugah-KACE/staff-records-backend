from uuid import UUID
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.new.schemas import employment_history as schemas
from Apis.new.services.employment_history import employment_history_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

employment_history_router = APIRouter(prefix="/employment_histories")


@employment_history_router.get(
    "",
    response_model=List[schemas.EmploymentHistorySchema],
)
async def list_employment_histories(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
        employee_id: Optional[UUID] = None,
) -> Any:
    employment_histories = await actions.list_employment_histories(
        db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
    )
    return employment_histories


@employment_history_router.post(
    "",
    response_model=schemas.EmploymentHistorySchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_employment_history(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.EmploymentHistoryCreate
) -> Any:
    employment_history = await actions.create_employment_history(db=db, data=data)
    return employment_history


@employment_history_router.put(
    "/{id}",
    response_model=schemas.EmploymentHistorySchema,
)
async def update_employment_history(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.EmploymentHistoryUpdate,
) -> Any:
    employment_history = await actions.update_employment_history(db=db, id=id, data=data)
    return employment_history


@employment_history_router.get(
    "/{id}",
    response_model=schemas.EmploymentHistorySchema,
)
async def get_employment_history(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    employment_history = await actions.get_employment_history(db=db, id=id)
    return employment_history


@employment_history_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_employment_history(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_employment_history(db=db, id=id)
