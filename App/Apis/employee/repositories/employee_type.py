from Apis.employee.schemas.employee_type import (
    EmployeeTypeCreate, EmployeeTypeUpdate
)
from Apis.employee.generic_crud import CRUDBase
from Models.models import EmployeeType


class CRUDEmployeeType(CRUDBase[EmployeeType, EmployeeTypeCreate, EmployeeTypeUpdate]):
    pass


employee_type_actions = CRUDEmployeeType(EmployeeType)
