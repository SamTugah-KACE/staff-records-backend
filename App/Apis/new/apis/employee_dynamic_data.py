from uuid import UUID
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.new.schemas import employee_dynamic_data as schemas
from Apis.new.services.employee_dynamic_data import employee_dynamic_data_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

employee_dynamic_data_router = APIRouter(prefix="/employee_dynamic_datas")


@employee_dynamic_data_router.get(
    "",
    response_model=List[schemas.EmployeeDynamicDataSchema],
)
async def list_employee_dynamic_datas(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        employee_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
) -> Any:
    employee_dynamic_datas = await actions.list_employee_dynamic_datas(
        db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
    )
    return employee_dynamic_datas


@employee_dynamic_data_router.post(
    "",
    response_model=schemas.EmployeeDynamicDataSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee_dynamic_data(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.EmployeeDynamicDataCreate
) -> Any:
    employee_dynamic_data = await actions.create_employee_dynamic_data(db=db, data=data)
    return employee_dynamic_data


@employee_dynamic_data_router.put(
    "/{id}",
    response_model=schemas.EmployeeDynamicDataSchema,
)
async def update_employee_dynamic_data(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.EmployeeDynamicDataUpdate,
) -> Any:
    employee_dynamic_data = await actions.update_employee_dynamic_data(db=db, id=id, data=data)
    return employee_dynamic_data


@employee_dynamic_data_router.get(
    "/{id}",
    response_model=schemas.EmployeeDynamicDataSchema,
)
async def get_employee_dynamic_data(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    employee_dynamic_data = await actions.get_employee_dynamic_data(db=db, id=id)
    return employee_dynamic_data


@employee_dynamic_data_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_employee_dynamic_data(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_employee_dynamic_data(db=db, id=id)
