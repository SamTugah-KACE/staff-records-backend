from typing import List, Optional, Literal

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.employee.repositories.professional_qualification import professional_qualification_actions as professional_qualification_repo
from Apis.employee.schemas.professional_qualification import ProfessionalQualificationSchema, ProfessionalQualificationUpdate, ProfessionalQualificationCreate


class ProfessionalQualificationService:

    def __init__(self):
        self.repo = professional_qualification_repo

    async def list_professional_qualifications(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
            employee_id: Optional[UUID4] = None,
    ) -> List[ProfessionalQualificationSchema]:
        professional_qualifications = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
        )
        return professional_qualifications

    async def create_professional_qualification(self, db: Session, *, data: ProfessionalQualificationCreate) -> ProfessionalQualificationSchema:
        professional_qualification = self.repo.create(db=db, data=data)
        return professional_qualification

    async def update_professional_qualification(self, db: Session, *, id: UUID4, data: ProfessionalQualificationUpdate) -> ProfessionalQualificationSchema:
        professional_qualification = self.repo.get_by_id(db=db, id=id)
        professional_qualification = self.repo.update(db=db, db_obj=professional_qualification, data=data)
        return professional_qualification

    async def get_professional_qualification(self, db: Session, *, id: UUID4) -> ProfessionalQualificationSchema:
        professional_qualification = self.repo.get_by_id(db=db, id=id)
        return professional_qualification

    async def delete_professional_qualification(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_professional_qualification_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[ProfessionalQualificationSchema]:
        professional_qualifications = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return professional_qualifications

    async def search_professional_qualifications(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[ProfessionalQualificationSchema]:
        professional_qualifications = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return professional_qualifications


professional_qualification_service = ProfessionalQualificationService()
