from typing import List, Optional

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.employee.repositories.academic_qualification import academic_qualification_actions as academic_qualification_repo
from Apis.employee.schemas.academic_qualification import AcademicQualificationSchema, AcademicQualificationUpdate, AcademicQualificationCreate


class AcademicQualificationService:

    def __init__(self):
        self.repo = academic_qualification_repo

    async def list_academic_qualifications(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
            employee_id: Optional[UUID4] = None,
    ) -> List[AcademicQualificationSchema]:
        academic_qualifications = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
        )
        return academic_qualifications

    async def create_academic_qualification(self, db: Session, *, data: AcademicQualificationCreate) -> AcademicQualificationSchema:
        academic_qualification = self.repo.create(db=db, data=data)
        return academic_qualification

    async def update_academic_qualification(self, db: Session, *, id: UUID4, data: AcademicQualificationUpdate) -> AcademicQualificationSchema:
        academic_qualification = self.repo.get_by_id(db=db, id=id)
        academic_qualification = self.repo.update(db=db, db_obj=academic_qualification, data=data)
        return academic_qualification

    async def get_academic_qualification(self, db: Session, *, id: UUID4) -> AcademicQualificationSchema:
        academic_qualification = self.repo.get_by_id(db=db, id=id)
        return academic_qualification

    async def delete_academic_qualification(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_academic_qualification_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[AcademicQualificationSchema]:
        academic_qualifications = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return academic_qualifications

    async def search_academic_qualifications(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[AcademicQualificationSchema]:
        academic_qualifications = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return academic_qualifications


academic_qualification_service = AcademicQualificationService()
