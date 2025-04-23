from typing import Optional

from pydantic import BaseModel
from pydantic import UUID4


# AcademicQualification
class AcademicQualificationBase(BaseModel):
    organization_id: Optional[UUID4] = None
    employee_id: Optional[UUID4] = None
    degree: Optional[str] = None
    institution: Optional[str] = None
    year_obtained: Optional[int] = None
    details: Optional[dict] = None
    certificate_path: Optional[str] = None


# Properties to receive via API on creation
class AcademicQualificationCreate(AcademicQualificationBase):
    employee_id: UUID4
    degree: str
    institution: str
    year_obtained: int


# Properties to receive via API on update
class AcademicQualificationUpdate(AcademicQualificationBase):
    pass


class AcademicQualificationInDBBase(AcademicQualificationBase):
    id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class AcademicQualificationSchema(AcademicQualificationInDBBase):
    pass
