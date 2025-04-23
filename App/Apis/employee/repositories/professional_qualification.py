from Apis.employee.schemas.professional_qualification import (
    ProfessionalQualificationCreate, ProfessionalQualificationUpdate
)
from Apis.employee.generic_crud import CRUDBase
from Models.models import ProfessionalQualification


class CRUDProfessionalQualification(
    CRUDBase[ProfessionalQualification, ProfessionalQualificationCreate, ProfessionalQualificationUpdate]
):
    pass


professional_qualification_actions = CRUDProfessionalQualification(ProfessionalQualification)
