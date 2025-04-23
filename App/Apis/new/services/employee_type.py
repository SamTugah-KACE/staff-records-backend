from typing import List, Optional, Literal

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.new.repositories.employee_type import employee_type_actions as employee_type_repo
from Apis.new.schemas.employee_type import EmployeeTypeSchema, EmployeeTypeUpdate, EmployeeTypeCreate


class EmployeeTypeService:

    def __init__(self):
        self.repo = employee_type_repo

    async def list_employee_types(
            self, db: Session, *,
            organization_id: UUID4,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
    ) -> List[EmployeeTypeSchema]:
        employee_types = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, organization_id=organization_id
        )
        return employee_types

    async def create_employee_type(self, db: Session, *, data: EmployeeTypeCreate) -> EmployeeTypeSchema:
        employee_type = self.repo.create(db=db, data=data)
        return employee_type

    async def update_employee_type(self, db: Session, *, id: UUID4, data: EmployeeTypeUpdate) -> EmployeeTypeSchema:
        employee_type = self.repo.get_by_id(db=db, id=id)
        employee_type = self.repo.update(db=db, db_obj=employee_type, data=data)
        return employee_type

    async def get_employee_type(self, db: Session, *, id: UUID4) -> EmployeeTypeSchema:
        employee_type = self.repo.get_by_id(db=db, id=id)
        return employee_type

    async def delete_employee_type(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_employee_type_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[EmployeeTypeSchema]:
        employee_types = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return employee_types

    async def search_employee_types(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[EmployeeTypeSchema]:
        employee_types = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return employee_types


employee_type_service = EmployeeTypeService()
