from typing import List, Optional, Literal

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.employee.repositories.salary_payment import salary_payment_actions as salary_payment_repo
from Apis.employee.schemas.salary_payment import SalaryPaymentSchema, SalaryPaymentUpdate, SalaryPaymentCreate


class SalaryPaymentService:

    def __init__(self):
        self.repo = salary_payment_repo

    async def list_salary_payments(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
            employee_id: Optional[UUID4] = None,
    ) -> List[SalaryPaymentSchema]:
        salary_payments = self.repo.get_all(
            db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
        )
        return salary_payments

    async def create_salary_payment(self, db: Session, *, data: SalaryPaymentCreate) -> SalaryPaymentSchema:
        salary_payment = self.repo.create(db=db, data=data)
        return salary_payment

    async def update_salary_payment(self, db: Session, *, id: UUID4, data: SalaryPaymentUpdate) -> SalaryPaymentSchema:
        salary_payment = self.repo.get_by_id(db=db, id=id)
        salary_payment = self.repo.update(db=db, db_obj=salary_payment, data=data)
        return salary_payment

    async def get_salary_payment(self, db: Session, *, id: UUID4) -> SalaryPaymentSchema:
        salary_payment = self.repo.get_by_id(db=db, id=id)
        return salary_payment

    async def delete_salary_payment(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_salary_payment_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[SalaryPaymentSchema]:
        salary_payments = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return salary_payments

    async def search_salary_payments(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[SalaryPaymentSchema]:
        salary_payments = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return salary_payments


salary_payment_service = SalaryPaymentService()
