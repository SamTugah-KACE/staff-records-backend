from typing import List, Optional, Literal

from pydantic import UUID4
from sqlalchemy.orm import Session

from Apis.new.repositories.emergency_contact import emergency_contact_actions as emergency_contact_repo
from Apis.new.schemas.emergency_contact import EmergencyContactSchema, EmergencyContactUpdate, EmergencyContactCreate


class EmergencyContactService:

    def __init__(self):
        self.repo = emergency_contact_repo

    async def list_emergency_contacts(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: str = None,
            employee_id: Optional[UUID4] = None,
    ) -> List[EmergencyContactSchema]:
        emergency_contacts = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
        )
        return emergency_contacts

    async def create_emergency_contact(self, db: Session, *, data: EmergencyContactCreate) -> EmergencyContactSchema:
        emergency_contact = self.repo.create(db=db, data=data)
        return emergency_contact

    async def update_emergency_contact(self, db: Session, *, id: UUID4, data: EmergencyContactUpdate) -> EmergencyContactSchema:
        emergency_contact = self.repo.get_by_id(db=db, id=id)
        emergency_contact = self.repo.update(db=db, db_obj=emergency_contact, data=data)
        return emergency_contact

    async def get_emergency_contact(self, db: Session, *, id: UUID4) -> EmergencyContactSchema:
        emergency_contact = self.repo.get_by_id(db=db, id=id)
        return emergency_contact

    async def delete_emergency_contact(self, db: Session, *, id: UUID4) -> None:
        self.repo.delete(db=db, id=id, soft=False)

    async def get_emergency_contact_by_keywords(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[EmergencyContactSchema]:
        emergency_contacts = self.repo.get_by_filters(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return emergency_contacts

    async def search_emergency_contacts(
            self, db: Session, *,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **kwargs
    ) -> List[EmergencyContactSchema]:
        emergency_contacts = self.repo.get_by_pattern(
            db=db, skip=skip, limit=limit, order_by=order_by, **kwargs
        )
        return emergency_contacts


emergency_contact_service = EmergencyContactService()
