from .backend.strategies import StrategyFirstBackend
from .models import Strategy

CODENAME_MAP = {
    Strategy.Codename.STRATEGY_1: StrategyFirstBackend,
}
