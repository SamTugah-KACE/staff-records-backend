from typing import Optional

from pydantic import BaseModel
from pydantic import UUID4


# EmployeePaymentDetail
class EmployeePaymentDetailsBase(BaseModel):
    employee_id: Optional[UUID4] = None
    payment_mode: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    mobile_money_provider: Optional[str] = None
    wallet_number: Optional[str] = None
    additional_info: Optional[dict] = None
    is_verified: Optional[bool] = False


# Properties to receive via API on creation
class EmployeePaymentDetailsCreate(EmployeePaymentDetailsBase):
    employee_id: UUID4
    payment_mode: str


# Properties to receive via API on update
class EmployeePaymentDetailsUpdate(EmployeePaymentDetailsBase):
    pass


class EmployeePaymentDetailsInDBBase(EmployeePaymentDetailsBase):
    id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class EmployeePaymentDetailsSchema(EmployeePaymentDetailsInDBBase):
    pass
