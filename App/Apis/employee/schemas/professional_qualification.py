from typing import Optional

from pydantic import BaseModel
from pydantic import UUID4


# ProfessionalQualification
class ProfessionalQualificationBase(BaseModel):
    employee_id: Optional[UUID4] = None
    qualification_name: Optional[str] = None
    institution: Optional[str] = None
    year_obtained: Optional[int] = None
    details: Optional[dict] = None
    license_path: Optional[str] = None


# Properties to receive via API on creation
class ProfessionalQualificationCreate(ProfessionalQualificationBase):
    employee_id: UUID4
    qualification_name: str
    institution: str
    year_obtained: int


# Properties to receive via API on update
class ProfessionalQualificationUpdate(ProfessionalQualificationBase):
    pass


class ProfessionalQualificationInDBBase(ProfessionalQualificationBase):
    id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class ProfessionalQualificationSchema(ProfessionalQualificationInDBBase):
    pass
