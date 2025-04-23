from uuid import UUID
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.new.schemas import employee_payment_details as schemas
from Apis.new.services.employee_payment_details import employee_payment_details_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

employee_payment_details_router = APIRouter(prefix="/employee_payment_detail")


@employee_payment_details_router.get(
    "",
    response_model=List[schemas.EmployeePaymentDetailsSchema],
)
async def list_employee_payment_detail(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        employee_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
) -> Any:
    employee_payment_detail = await actions.list_employee_payment_detail(
        db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
    )
    return employee_payment_detail


@employee_payment_details_router.post(
    "",
    response_model=schemas.EmployeePaymentDetailsSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee_payment_details(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.EmployeePaymentDetailsCreate
) -> Any:
    employee_payment_details = await actions.create_employee_payment_details(db=db, data=data)
    return employee_payment_details


@employee_payment_details_router.put(
    "/{id}",
    response_model=schemas.EmployeePaymentDetailsSchema,
)
async def update_employee_payment_details(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.EmployeePaymentDetailsUpdate,
) -> Any:
    employee_payment_details = await actions.update_employee_payment_details(db=db, id=id, data=data)
    return employee_payment_details


@employee_payment_details_router.get(
    "/{id}",
    response_model=schemas.EmployeePaymentDetailsSchema,
)
async def get_employee_payment_details(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    employee_payment_details = await actions.get_employee_payment_details(db=db, id=id)
    return employee_payment_details


@employee_payment_details_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_employee_payment_details(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_employee_payment_details(db=db, id=id)
