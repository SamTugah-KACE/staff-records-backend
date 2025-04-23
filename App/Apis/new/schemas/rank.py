from typing import Optional

from pydantic import BaseModel
from pydantic import UUID4


# Rank
class RankBase(BaseModel):
    organization_id: Optional[UUID4] = None
    name: Optional[str] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    currency: Optional[str] = "GHS"
    conversion_info: Optional[str] = None


# Properties to receive via API on creation
class RankCreate(RankBase):
    organization_id: UUID4
    name: str
    min_salary: float


# Properties to receive via API on update
class RankUpdate(RankBase):
    pass


class RankInDBBase(RankBase):
    id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class RankSchema(RankInDBBase):
    pass
