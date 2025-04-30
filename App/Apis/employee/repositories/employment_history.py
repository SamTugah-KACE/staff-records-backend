from Apis.employee.schemas.employment_history import (
    EmploymentHistoryCreate, EmploymentHistoryUpdate
)
from Apis.employee.generic_crud import CRUDBase
from Models.models import EmploymentHistory


class CRUDEmploymentHistory(CRUDBase[EmploymentHistory, EmploymentHistoryCreate, EmploymentHistoryUpdate]):
    pass


employment_history_actions = CRUDEmploymentHistory(EmploymentHistory)
