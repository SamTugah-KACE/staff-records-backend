from typing import List, Optional, Literal

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.employee.repositories.promotion_request import promotion_request_actions as promotion_request_repo
from Apis.employee.schemas.promotion_request import PromotionRequestSchema, PromotionRequestUpdate, PromotionRequestCreate


class PromotionRequestService:

    def __init__(self):
        self.repo = promotion_request_repo

    async def list_promotion_requests(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
            employee_id: Optional[UUID4] = None,
    ) -> List[PromotionRequestSchema]:
        promotion_requests = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
        )
        return promotion_requests

    async def create_promotion_request(self, db: Session, *, data: PromotionRequestCreate) -> PromotionRequestSchema:
        promotion_request = self.repo.create(db=db, data=data)
        return promotion_request

    async def update_promotion_request(self, db: Session, *, id: UUID4, data: PromotionRequestUpdate) -> PromotionRequestSchema:
        promotion_request = self.repo.get_by_id(db=db, id=id)
        promotion_request = self.repo.update(db=db, db_obj=promotion_request, data=data)
        return promotion_request

    async def get_promotion_request(self, db: Session, *, id: UUID4) -> PromotionRequestSchema:
        promotion_request = self.repo.get_by_id(db=db, id=id)
        return promotion_request

    async def delete_promotion_request(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_promotion_request_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[PromotionRequestSchema]:
        promotion_requests = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return promotion_requests

    async def search_promotion_requests(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[PromotionRequestSchema]:
        promotion_requests = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return promotion_requests


promotion_request_service = PromotionRequestService()
