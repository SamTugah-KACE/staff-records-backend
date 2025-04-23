from uuid import UUID
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.new.schemas import professional_qualification as schemas
from Apis.new.services.professional_qualification import professional_qualification_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

professional_qualification_router = APIRouter(prefix="/professional_qualifications")


@professional_qualification_router.get(
    "",
    response_model=List[schemas.ProfessionalQualificationSchema],
)
async def list_professional_qualifications(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        employee_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
) -> Any:
    professional_qualifications = await actions.list_professional_qualifications(
        db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
    )
    return professional_qualifications


@professional_qualification_router.post(
    "",
    response_model=schemas.ProfessionalQualificationSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_professional_qualification(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.ProfessionalQualificationCreate
) -> Any:
    professional_qualification = await actions.create_professional_qualification(db=db, data=data)
    return professional_qualification


@professional_qualification_router.put(
    "/{id}",
    response_model=schemas.ProfessionalQualificationSchema,
)
async def update_professional_qualification(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.ProfessionalQualificationUpdate,
) -> Any:
    professional_qualification = await actions.update_professional_qualification(db=db, id=id, data=data)
    return professional_qualification


@professional_qualification_router.get(
    "/{id}",
    response_model=schemas.ProfessionalQualificationSchema,
)
async def get_professional_qualification(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    professional_qualification = await actions.get_professional_qualification(db=db, id=id)
    return professional_qualification


@professional_qualification_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_professional_qualification(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_professional_qualification(db=db, id=id)
