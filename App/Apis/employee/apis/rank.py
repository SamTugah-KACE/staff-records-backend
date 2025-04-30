from uuid import UUID
from typing import Any, List, Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from Apis.employee.schemas import rank as schemas
from Apis.employee.services.rank import rank_service as actions
from Crud.auth import get_current_user
from Models.models import User
from database.db_session import get_db

rank_router = APIRouter(prefix="/ranks")


@rank_router.get(
    "",
    response_model=List[schemas.RankSchema],
)
async def list_ranks(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
) -> Any:
    ranks = await actions.list_ranks(
        db=db, skip=skip, limit=limit, order_by=order_by, organization_id=current_user.get('organization_id')
    )
    return ranks


@rank_router.post(
    "",
    response_model=schemas.RankSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_rank(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        data: schemas.RankCreate
) -> Any:
    rank = await actions.create_rank(db=db, data=data)
    return rank


@rank_router.put(
    "/{id}",
    response_model=schemas.RankSchema,
)
async def update_rank(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID,
        data: schemas.RankUpdate,
) -> Any:
    rank = await actions.update_rank(db=db, id=id, data=data)
    return rank


@rank_router.get(
    "/{id}",
    response_model=schemas.RankSchema,
)
async def get_rank(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> Any:
    rank = await actions.get_rank(db=db, id=id)
    return rank


@rank_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_rank(
        *, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        id: UUID
) -> None:
    await actions.delete_rank(db=db, id=id)
