from typing import Optional

from pydantic import BaseModel
from pydantic import UUID4


# EmergencyContact
class EmergencyContactBase(BaseModel):
    employee_id: Optional[UUID4] = None
    name: Optional[str] = None
    relation: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    details: Optional[dict] = None


# Properties to receive via API on creation
class EmergencyContactCreate(EmergencyContactBase):
    employee_id: UUID4
    name: str
    relation: str
    phone: str


# Properties to receive via API on update
class EmergencyContactUpdate(EmergencyContactBase):
    pass


class EmergencyContactInDBBase(EmergencyContactBase):
    id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class EmergencyContactSchema(EmergencyContactInDBBase):
    pass
