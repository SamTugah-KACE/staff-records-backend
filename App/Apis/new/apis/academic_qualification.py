from uuid import UUID
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.new.schemas import academic_qualification as schemas
from Apis.new.services.academic_qualification import academic_qualification_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

academic_qualification_router = APIRouter(prefix="/academic_qualifications")


@academic_qualification_router.get(
    "",
    response_model=List[schemas.AcademicQualificationSchema],
)
async def list_academic_qualifications(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        employee_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
) -> Any:
    academic_qualifications = await actions.list_academic_qualifications(
        db=db, skip=skip, limit=limit, order_by=order_by, employee_id=employee_id
    )
    return academic_qualifications


@academic_qualification_router.post(
    "",
    response_model=schemas.AcademicQualificationSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_academic_qualification(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.AcademicQualificationCreate
) -> Any:
    academic_qualification = await actions.create_academic_qualification(db=db, data=data)
    return academic_qualification


@academic_qualification_router.put(
    "/{id}",
    response_model=schemas.AcademicQualificationSchema,
)
async def update_academic_qualification(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.AcademicQualificationUpdate,
) -> Any:
    academic_qualification = await actions.update_academic_qualification(db=db, id=id, data=data)
    return academic_qualification


@academic_qualification_router.get(
    "/{id}",
    response_model=schemas.AcademicQualificationSchema,
)
async def get_academic_qualification(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    academic_qualification = await actions.get_academic_qualification(db=db, id=id)
    return academic_qualification


@academic_qualification_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_academic_qualification(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_academic_qualification(db=db, id=id)
