from datetime import date
from typing import Optional

from pydantic import BaseModel
from pydantic import UUID4


# EmploymentHistory
class EmploymentHistoryBase(BaseModel):
    employee_id: Optional[UUID4] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    details: Optional[dict] = None
    documents_path: Optional[str] = None


# Properties to receive via API on creation
class EmploymentHistoryCreate(EmploymentHistoryBase):
    employee_id: UUID4
    job_title: str
    company: str
    start_date: date


# Properties to receive via API on update
class EmploymentHistoryUpdate(EmploymentHistoryBase):
    pass


class EmploymentHistoryInDBBase(EmploymentHistoryBase):
    id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class EmploymentHistorySchema(EmploymentHistoryInDBBase):
    pass
