from typing import List, Optional, Literal

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.employee.repositories.next_of_kin import next_of_kin_actions as next_of_kin_repo
from Apis.employee.schemas.next_of_kin import NextOfKinSchema, NextOfKinUpdate, NextOfKinCreate


class NextOfKinService:

    def __init__(self):
        self.repo = next_of_kin_repo

    async def list_next_of_kins(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
            employee_id: Optional[UUID4] = None,
    ) -> List[NextOfKinSchema]:
        next_of_kins = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
        )
        return next_of_kins

    async def create_next_of_kin(self, db: Session, *, data: NextOfKinCreate) -> NextOfKinSchema:
        next_of_kin = self.repo.create(db=db, data=data)
        return next_of_kin

    async def update_next_of_kin(self, db: Session, *, id: UUID4, data: NextOfKinUpdate) -> NextOfKinSchema:
        next_of_kin = self.repo.get_by_id(db=db, id=id)
        next_of_kin = self.repo.update(db=db, db_obj=next_of_kin, data=data)
        return next_of_kin

    async def get_next_of_kin(self, db: Session, *, id: UUID4) -> NextOfKinSchema:
        next_of_kin = self.repo.get_by_id(db=db, id=id)
        return next_of_kin

    async def delete_next_of_kin(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_next_of_kin_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[NextOfKinSchema]:
        next_of_kins = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return next_of_kins

    async def search_next_of_kins(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[NextOfKinSchema]:
        next_of_kins = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return next_of_kins


next_of_kin_service = NextOfKinService()
