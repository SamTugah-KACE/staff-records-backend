from typing import List, Optional, Literal

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.employee.repositories.department import department_actions as department_repo
from Apis.employee.schemas.department import DepartmentSchema, DepartmentUpdate, DepartmentCreate


class DepartmentService:

    def __init__(self):
        self.repo = department_repo

    async def list_departments(
            self, db: Session, *,
            organization_id: UUID4,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
    ) -> List[DepartmentSchema]:
        departments = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, organization_id=organization_id
        )
        return departments

    async def create_department(self, db: Session, *, data: DepartmentCreate) -> DepartmentSchema:
        department = self.repo.create(db=db, data=data)
        return department

    async def update_department(self, db: Session, *, id: UUID4, data: DepartmentUpdate) -> DepartmentSchema:
        department = self.repo.get_by_id(db=db, id=id)
        department = self.repo.update(db=db, db_obj=department, data=data)
        return department

    async def get_department(self, db: Session, *, id: UUID4) -> DepartmentSchema:
        department = self.repo.get_by_id(db=db, id=id)
        return department

    async def delete_department(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_department_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[DepartmentSchema]:
        departments = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return departments

    async def search_departments(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[DepartmentSchema]:
        departments = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return departments


department_service = DepartmentService()
