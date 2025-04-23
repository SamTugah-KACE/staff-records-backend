from Apis.new.schemas.professional_qualification import (
    ProfessionalQualificationCreate, ProfessionalQualificationUpdate
)
from Apis.new.generic_crud import CRUDBase
from Models.models import ProfessionalQualification


class CRUDProfessionalQualification(
    CRUDBase[ProfessionalQualification, ProfessionalQualificationCreate, ProfessionalQualificationUpdate]
):
    pass


professional_qualification_actions = CRUDProfessionalQualification(ProfessionalQualification)
