from Apis.new.generic_crud import CRUDBase
from Apis.new.schemas.employee_payment_details import (
    EmployeePaymentDetailsCreate, EmployeePaymentDetailsUpdate
)
from Models.models import EmployeePaymentDetail


class CRUDEmployeePaymentDetail(
    CRUDBase[EmployeePaymentDetail, EmployeePaymentDetailsCreate, EmployeePaymentDetailsUpdate]
):
    pass


employee_payment_detail_actions = CRUDEmployeePaymentDetail(EmployeePaymentDetail)
