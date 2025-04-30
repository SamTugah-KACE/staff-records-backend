from Apis.employee.schemas.salary_payment import (
    SalaryPaymentCreate, SalaryPaymentUpdate
)
from Apis.employee.generic_crud import CRUDBase
from Models.models import SalaryPayment


class CRUDSalaryPayment(CRUDBase[SalaryPayment, SalaryPaymentCreate, SalaryPaymentUpdate]):
    pass


salary_payment_actions = CRUDSalaryPayment(SalaryPayment)
