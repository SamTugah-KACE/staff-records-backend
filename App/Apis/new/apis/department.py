from uuid import UUID
from typing import Any, List, Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.new.schemas import department as schemas
from Apis.new.services.department import department_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

department_router = APIRouter(prefix="/departments")


@department_router.get(
    "",
    response_model=List[schemas.DepartmentSchema],
)
async def list_departments(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
) -> Any:
    departments = await actions.list_departments(
        db=db, skip=skip, limit=limit, order_by=order_by, organization_id=current_user.get('organization_id')
    )
    return departments


@department_router.post(
    "",
    response_model=schemas.DepartmentSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_department(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.DepartmentCreate
) -> Any:
    department = await actions.create_department(db=db, data=data)
    return department


@department_router.put(
    "/{id}",
    response_model=schemas.DepartmentSchema,
)
async def update_department(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.DepartmentUpdate,
) -> Any:
    department = await actions.update_department(db=db, id=id, data=data)
    return department


@department_router.get(
    "/{id}",
    response_model=schemas.DepartmentSchema,
)
async def get_department(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    department = await actions.get_department(db=db, id=id)
    return department


@department_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_department(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_department(db=db, id=id)
