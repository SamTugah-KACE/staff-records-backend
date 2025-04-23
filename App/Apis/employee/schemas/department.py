from datetime import date, datetime, time
from typing import Optional, Any, Dict

from pydantic import BaseModel
from pydantic import UUID4


# Department
class DepartmentBase(BaseModel):
    name: Optional[str] = None
    department_head_id: Optional[UUID4] = None
    branch_id: Optional[UUID4] = None
    organization_id: Optional[UUID4] = None


# Properties to receive via API on creation
class DepartmentCreate(DepartmentBase):
    name: str
    department_head_id: Optional[UUID4] = None
    branch_id: Optional[UUID4] = None
    organization_id: UUID4


# Properties to receive via API on update
class DepartmentUpdate(DepartmentBase):
    pass


class DepartmentInDBBase(DepartmentBase):
    id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class DepartmentSchema(DepartmentInDBBase):
    pass
