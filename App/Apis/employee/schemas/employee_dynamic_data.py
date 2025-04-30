from datetime import date, datetime, time
from typing import Optional, Any, Dict

from pydantic import BaseModel
from pydantic import UUID4


# EmployeeDynamicData
class EmployeeDynamicDataBase(BaseModel):
    employee_id: Optional[UUID4] = None
    data_category: Optional[str] = None
    data: Optional[dict] = None


# Properties to receive via API on creation
class EmployeeDynamicDataCreate(EmployeeDynamicDataBase):
    employee_id: UUID4
    data_category: str
    data: dict


# Properties to receive via API on update
class EmployeeDynamicDataUpdate(EmployeeDynamicDataBase):
    pass


class EmployeeDynamicDataInDBBase(EmployeeDynamicDataBase):
    id: Optional[UUID4] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class EmployeeDynamicDataSchema(EmployeeDynamicDataInDBBase):
    pass
