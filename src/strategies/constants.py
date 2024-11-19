from .models import Strategy
from .backend.strategies import StrategyFirstBackend


CODENAME_MAP = {
    Strategy.Codename.STRATEGY_1: StrategyFirstBackend,
}
