from Apis.employee.schemas.promotion_request import (
    PromotionRequestCreate, PromotionRequestUpdate
)
from Apis.employee.generic_crud import CRUDBase
from Models.models import PromotionRequest


class CRUDPromotionRequest(CRUDBase[PromotionRequest, PromotionRequestCreate, PromotionRequestUpdate]):
    pass


promotion_request_actions = CRUDPromotionRequest(PromotionRequest)
