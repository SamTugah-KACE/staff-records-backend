from typing import List, Optional, Literal

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.new.repositories.rank import rank_actions as rank_repo
from Apis.new.schemas.rank import RankSchema, RankUpdate, RankCreate


class RankService:

    def __init__(self):
        self.repo = rank_repo

    async def list_ranks(
            self, db: Session, *,
            organization_id: UUID4,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
    ) -> List[RankSchema]:
        ranks = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, organization_id=organization_id
        )
        return ranks

    async def create_rank(self, db: Session, *, data: RankCreate) -> RankSchema:
        rank = self.repo.create(db=db, data=data)
        return rank

    async def update_rank(self, db: Session, *, id: UUID4, data: RankUpdate) -> RankSchema:
        rank = self.repo.get_by_id(db=db, id=id)
        rank = self.repo.update(db=db, db_obj=rank, data=data)
        return rank

    async def get_rank(self, db: Session, *, id: UUID4) -> RankSchema:
        rank = self.repo.get_by_id(db=db, id=id)
        return rank

    async def delete_rank(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_rank_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[RankSchema]:
        ranks = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return ranks

    async def search_ranks(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[RankSchema]:
        ranks = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return ranks


rank_service = RankService()
