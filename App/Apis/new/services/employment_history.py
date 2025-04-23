from typing import List, Optional, Literal

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.new.repositories.employment_history import employment_history_actions as employment_history_repo
from Apis.new.schemas.employment_history import EmploymentHistorySchema, EmploymentHistoryUpdate, EmploymentHistoryCreate


class EmploymentHistoryService:

    def __init__(self):
        self.repo = employment_history_repo

    async def list_employment_histories(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
            employee_id: Optional[UUID4] = None,
    ) -> List[EmploymentHistorySchema]:
        employment_histories = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
        )
        return employment_histories

    async def create_employment_history(self, db: Session, *, data: EmploymentHistoryCreate) -> EmploymentHistorySchema:
        employment_history = self.repo.create(db=db, data=data)
        return employment_history

    async def update_employment_history(self, db: Session, *, id: UUID4, data: EmploymentHistoryUpdate) -> EmploymentHistorySchema:
        employment_history = self.repo.get_by_id(db=db, id=id)
        employment_history = self.repo.update(db=db, db_obj=employment_history, data=data)
        return employment_history

    async def get_employment_history(self, db: Session, *, id: UUID4) -> EmploymentHistorySchema:
        employment_history = self.repo.get_by_id(db=db, id=id)
        return employment_history

    async def delete_employment_history(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_employment_history_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[EmploymentHistorySchema]:
        employment_histories = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return employment_histories

    async def search_employment_histories(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[EmploymentHistorySchema]:
        employment_histories = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return employment_histories


employment_history_service = EmploymentHistoryService()
