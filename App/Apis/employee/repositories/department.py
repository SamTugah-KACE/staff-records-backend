from Apis.employee.schemas.department import (
    DepartmentCreate, DepartmentUpdate
)
from Apis.employee.generic_crud import CRUDBase
from Models.models import Department


class CRUDDepartment(CRUDBase[Department, DepartmentCreate, DepartmentUpdate]):
    pass


department_actions = CRUDDepartment(Department)
