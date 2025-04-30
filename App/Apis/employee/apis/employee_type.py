from uuid import UUID
from typing import Any, List, Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.employee.schemas import employee_type as schemas
from Apis.employee.services.employee_type import employee_type_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

employee_type_router = APIRouter(prefix="/employee_types", tags=["Employee Type"])


@employee_type_router.get(
    "",
    response_model=List[schemas.EmployeeTypeSchema],
)
async def list_employee_types(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
) -> Any:
    employee_types = await actions.list_employee_types(
        db=db, skip=skip, limit=limit, order_by=order_by, organization_id=current_user.get('organization_id')
    )
    return employee_types


@employee_type_router.post(
    "",
    response_model=schemas.EmployeeTypeSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee_type(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.EmployeeTypeCreate
) -> Any:
    employee_type = await actions.create_employee_type(db=db, data=data)
    return employee_type


@employee_type_router.put(
    "/{id}",
    response_model=schemas.EmployeeTypeSchema,
)
async def update_employee_type(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.EmployeeTypeUpdate,
) -> Any:
    employee_type = await actions.update_employee_type(db=db, id=id, data=data)
    return employee_type


@employee_type_router.get(
    "/{id}",
    response_model=schemas.EmployeeTypeSchema,
)
async def get_employee_type(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    employee_type = await actions.get_employee_type(db=db, id=id)
    return employee_type


@employee_type_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_employee_type(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_employee_type(db=db, id=id)
