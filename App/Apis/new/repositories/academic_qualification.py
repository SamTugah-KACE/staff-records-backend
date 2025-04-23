from Apis.new.schemas.academic_qualification import (
    AcademicQualificationCreate, AcademicQualificationUpdate
)
from Apis.new.generic_crud import CRUDBase
from Models.models import AcademicQualification


class CRUDAcademicQualification(
    CRUDBase[AcademicQualification, AcademicQualificationCreate, AcademicQualificationUpdate]
):
    pass


academic_qualification_actions = CRUDAcademicQualification(AcademicQualification)
