from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import UUID4


# PromotionRequest
class PromotionRequestBase(BaseModel):
    employee_id: Optional[UUID4] = None
    current_rank_id: Optional[UUID4] = None
    proposed_rank_id: Optional[UUID4] = None
    request_date: Optional[datetime] = None
    promotion_effective_date: Optional[datetime] = None
    department_approved: Optional[bool] = False
    department_approval_date: Optional[datetime] = None
    hr_approved: Optional[bool] = False
    hr_approval_date: Optional[datetime] = None
    evidence_documents: Optional[dict] = None
    comments: Optional[str] = None


# Properties to receive via API on creation
class PromotionRequestCreate(PromotionRequestBase):
    employee_id: UUID4


# Properties to receive via API on update
class PromotionRequestUpdate(PromotionRequestBase):
    pass


class PromotionRequestInDBBase(PromotionRequestBase):
    id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class PromotionRequestSchema(PromotionRequestInDBBase):
    pass
