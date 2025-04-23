from Apis.new.schemas.promotion_request import (
    PromotionRequestCreate, PromotionRequestUpdate
)
from Apis.new.generic_crud import CRUDBase
from Models.models import PromotionRequest


class CRUDPromotionRequest(CRUDBase[PromotionRequest, PromotionRequestCreate, PromotionRequestUpdate]):
    pass


promotion_request_actions = CRUDPromotionRequest(PromotionRequest)
