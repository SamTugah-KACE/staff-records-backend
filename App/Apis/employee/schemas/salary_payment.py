from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import UUID4


# SalaryPayment
class SalaryPaymentBase(BaseModel):
    employee_id: Optional[UUID4] = None
    rank_id: Optional[UUID4] = None
    amount: Optional[float] = None
    currency: Optional[str] = "USD"
    payment_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    status: Optional[str] = "Success"
    approved_by: Optional[UUID4] = None


# Properties to receive via API on creation
class SalaryPaymentCreate(SalaryPaymentBase):
    employee_id: UUID4
    amount: float
    payment_method: str
    transaction_id: str


# Properties to receive via API on update
class SalaryPaymentUpdate(SalaryPaymentBase):
    pass


class SalaryPaymentInDBBase(SalaryPaymentBase):
    id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class SalaryPaymentSchema(SalaryPaymentInDBBase):
    pass
