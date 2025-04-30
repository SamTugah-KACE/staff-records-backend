from Apis.employee.generic_crud import CRUDBase
from Apis.employee.schemas.employee_payment_details import (
    EmployeePaymentDetailsCreate, EmployeePaymentDetailsUpdate
)
from Models.models import EmployeePaymentDetail


class CRUDEmployeePaymentDetail(
    CRUDBase[EmployeePaymentDetail, EmployeePaymentDetailsCreate, EmployeePaymentDetailsUpdate]
):
    pass


employee_payment_detail_actions = CRUDEmployeePaymentDetail(EmployeePaymentDetail)
