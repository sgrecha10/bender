from .backend.strategies import StrategyFirstBackend, AnnaStrategyBackend
from .models import Strategy

CODENAME_MAP = {
    Strategy.Codename.STRATEGY_1: StrategyFirstBackend,
    Strategy.Codename.STRATEGY_ANNA: AnnaStrategyBackend,
}
