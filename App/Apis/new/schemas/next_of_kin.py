from typing import Optional

from pydantic import BaseModel
from pydantic import UUID4


# NextOfKin
class NextOfKinBase(BaseModel):
    employee_id: Optional[UUID4] = None
    name: Optional[str] = None
    relation: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    details: Optional[dict] = None


# Properties to receive via API on creation
class NextOfKinCreate(NextOfKinBase):
    employee_id: UUID4
    name: str
    relation: str
    phone: str


# Properties to receive via API on update
class NextOfKinUpdate(NextOfKinBase):
    pass


class NextOfKinInDBBase(NextOfKinBase):
    id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class NextOfKinSchema(NextOfKinInDBBase):
    pass
