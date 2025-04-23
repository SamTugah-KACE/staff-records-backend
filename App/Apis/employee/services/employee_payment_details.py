from typing import List, Optional, Literal

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.employee.repositories.employee_payment_details import employee_payment_detail_actions as employee_payment_details_repo
from Apis.employee.schemas.employee_payment_details import EmployeePaymentDetailsSchema, EmployeePaymentDetailsUpdate, EmployeePaymentDetailsCreate


class EmployeePaymentDetailsService:

    def __init__(self):
        self.repo = employee_payment_details_repo

    async def list_employee_payment_detail(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
            employee_id: Optional[UUID4] = None,
    ) -> List[EmployeePaymentDetailsSchema]:
        employee_payment_detail = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
        )
        return employee_payment_detail

    async def create_employee_payment_details(self, db: Session, *, data: EmployeePaymentDetailsCreate) -> EmployeePaymentDetailsSchema:
        employee_payment_details = self.repo.create(db=db, data=data)
        return employee_payment_details

    async def update_employee_payment_details(self, db: Session, *, id: UUID4, data: EmployeePaymentDetailsUpdate) -> EmployeePaymentDetailsSchema:
        employee_payment_details = self.repo.get_by_id(db=db, id=id)
        employee_payment_details = self.repo.update(db=db, db_obj=employee_payment_details, data=data)
        return employee_payment_details

    async def get_employee_payment_details(self, db: Session, *, id: UUID4) -> EmployeePaymentDetailsSchema:
        employee_payment_details = self.repo.get_by_id(db=db, id=id)
        return employee_payment_details

    async def delete_employee_payment_details(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_employee_payment_details_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[EmployeePaymentDetailsSchema]:
        employee_payment_detail = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return employee_payment_detail

    async def search_employee_payment_detail(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[EmployeePaymentDetailsSchema]:
        employee_payment_detail = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return employee_payment_detail


employee_payment_details_service = EmployeePaymentDetailsService()
