from typing import List, Optional, Literal

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.employee.repositories.employee_dynamic_data import employee_dynamic_data_actions as employee_dynamic_data_repo
from Apis.employee.schemas.employee_dynamic_data import EmployeeDynamicDataSchema, EmployeeDynamicDataUpdate, EmployeeDynamicDataCreate


class EmployeeDynamicDataService:

    def __init__(self):
        self.repo = employee_dynamic_data_repo

    async def list_employee_dynamic_datas(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
            employee_id: Optional[UUID4] = None,
    ) -> List[EmployeeDynamicDataSchema]:
        employee_dynamic_datas = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
        )
        return employee_dynamic_datas

    async def create_employee_dynamic_data(self, db: Session, *, data: EmployeeDynamicDataCreate) -> EmployeeDynamicDataSchema:
        employee_dynamic_data = self.repo.create(db=db, data=data)
        return employee_dynamic_data

    async def update_employee_dynamic_data(self, db: Session, *, id: UUID4, data: EmployeeDynamicDataUpdate) -> EmployeeDynamicDataSchema:
        employee_dynamic_data = self.repo.get_by_id(db=db, id=id)
        employee_dynamic_data = self.repo.update(db=db, db_obj=employee_dynamic_data, data=data)
        return employee_dynamic_data

    async def get_employee_dynamic_data(self, db: Session, *, id: UUID4) -> EmployeeDynamicDataSchema:
        employee_dynamic_data = self.repo.get_by_id(db=db, id=id)
        return employee_dynamic_data

    async def delete_employee_dynamic_data(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_employee_dynamic_data_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[EmployeeDynamicDataSchema]:
        employee_dynamic_datas = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return employee_dynamic_datas

    async def search_employee_dynamic_datas(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[EmployeeDynamicDataSchema]:
        employee_dynamic_datas = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return employee_dynamic_datas


employee_dynamic_data_service = EmployeeDynamicDataService()
