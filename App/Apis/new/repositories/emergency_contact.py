from Apis.new.schemas.emergency_contact import (
    EmergencyContactCreate, EmergencyContactUpdate
)
from Apis.new.generic_crud import CRUDBase
from Models.models import EmergencyContact


class CRUDEmergencyContact(CRUDBase[EmergencyContact, EmergencyContactCreate, EmergencyContactUpdate]):
    pass


emergency_contact_actions = CRUDEmergencyContact(EmergencyContact)
