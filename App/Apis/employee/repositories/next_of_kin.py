from Apis.employee.schemas.next_of_kin import (
    NextOfKinCreate, NextOfKinUpdate
)
from Apis.employee.generic_crud import CRUDBase
from Models.models import NextOfKin


class CRUDNextOfKin(CRUDBase[NextOfKin, NextOfKinCreate, NextOfKinUpdate]):
    pass


next_of_kin_actions = CRUDNextOfKin(NextOfKin)
