from typing import Optional

from pydantic import BaseModel
from pydantic import UUID4


# EmployeeType
class EmployeeTypeBase(BaseModel):
    organization_id: Optional[UUID4] = None
    type_code: Optional[str] = None
    description: Optional[str] = None
    default_criteria: Optional[dict] = None


# Properties to receive via API on creation
class EmployeeTypeCreate(EmployeeTypeBase):
    organization_id: UUID4
    type_code: str


# Properties to receive via API on update
class EmployeeTypeUpdate(EmployeeTypeBase):
    pass


class EmployeeTypeInDBBase(EmployeeTypeBase):
    id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class EmployeeTypeSchema(EmployeeTypeInDBBase):
    pass
