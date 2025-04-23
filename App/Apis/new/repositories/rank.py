from Apis.new.schemas.rank import (
    RankCreate, RankUpdate
)
from Apis.new.generic_crud import CRUDBase
from Models.Tenants.organization import Rank


class CRUDRank(CRUDBase[Rank, RankCreate, RankUpdate]):
    pass


rank_actions = CRUDRank(Rank)
