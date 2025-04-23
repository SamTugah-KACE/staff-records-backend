from uuid import UUID
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.new.schemas import salary_payment as schemas
from Apis.new.services.salary_payment import salary_payment_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

salary_payment_router = APIRouter(prefix="/salary_payments")


@salary_payment_router.get(
    "",
    response_model=List[schemas.SalaryPaymentSchema],
)
async def list_salary_payments(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        employee_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
) -> Any:
    salary_payments = await actions.list_salary_payments(
        db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
    )
    return salary_payments


@salary_payment_router.post(
    "",
    response_model=schemas.SalaryPaymentSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_salary_payment(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.SalaryPaymentCreate
) -> Any:
    salary_payment = await actions.create_salary_payment(db=db, data=data)
    return salary_payment


@salary_payment_router.put(
    "/{id}",
    response_model=schemas.SalaryPaymentSchema,
)
async def update_salary_payment(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.SalaryPaymentUpdate,
) -> Any:
    salary_payment = await actions.update_salary_payment(db=db, id=id, data=data)
    return salary_payment


@salary_payment_router.get(
    "/{id}",
    response_model=schemas.SalaryPaymentSchema,
)
async def get_salary_payment(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    salary_payment = await actions.get_salary_payment(db=db, id=id)
    return salary_payment


@salary_payment_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_salary_payment(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_salary_payment(db=db, id=id)
