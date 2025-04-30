from uuid import UUID
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.employee.schemas import emergency_contact as schemas
from Apis.employee.services.emergency_contact import emergency_contact_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

emergency_contact_router = APIRouter(prefix="/emergency_contacts")


@emergency_contact_router.get(
    "",
    response_model=List[schemas.EmergencyContactSchema],
)
async def list_emergency_contacts(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        employee_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
) -> Any:
    emergency_contacts = await actions.list_emergency_contacts(
        db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
    )
    return emergency_contacts


@emergency_contact_router.post(
    "",
    response_model=schemas.EmergencyContactSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_emergency_contact(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.EmergencyContactCreate
) -> Any:
    emergency_contact = await actions.create_emergency_contact(db=db, data=data)
    return emergency_contact


@emergency_contact_router.put(
    "/{id}",
    response_model=schemas.EmergencyContactSchema,
)
async def update_emergency_contact(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.EmergencyContactUpdate,
) -> Any:
    emergency_contact = await actions.update_emergency_contact(db=db, id=id, data=data)
    return emergency_contact


@emergency_contact_router.get(
    "/{id}",
    response_model=schemas.EmergencyContactSchema,
)
async def get_emergency_contact(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    emergency_contact = await actions.get_emergency_contact(db=db, id=id)
    return emergency_contact


@emergency_contact_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_emergency_contact(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_emergency_contact(db=db, id=id)
