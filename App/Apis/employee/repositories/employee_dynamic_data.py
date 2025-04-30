from Apis.employee.schemas.employee_dynamic_data import (
    EmployeeDynamicDataCreate, EmployeeDynamicDataUpdate
)
from Apis.employee.generic_crud import CRUDBase
from Models.dynamic_models import EmployeeDynamicData


class CRUDEmployeeDynamicData(CRUDBase[EmployeeDynamicData, EmployeeDynamicDataCreate, EmployeeDynamicDataUpdate]):
    pass


employee_dynamic_data_actions = CRUDEmployeeDynamicData(EmployeeDynamicData)
