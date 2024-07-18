from strategies.models import Strategy
from decimal import Decimal

"""
1. 
"""


class MovingAverageBackend:
    def __init__(self, strategy: Strategy):
        self.strategy = strategy

    def get_current_moving_average(self) -> Decimal:
        return 4.23
