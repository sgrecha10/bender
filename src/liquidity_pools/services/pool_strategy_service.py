from datetime import datetime
from decimal import Decimal
from typing import Hashable, Optional

import pandas as pd

from liquidity_pools.models import Strategy
from liquidity_pools.services.range_price_service import RangePriceService
from liquidity_pools.services.standard_deviation_service import StandardDeviationService


class PoolStrategyService:
    def __init__(
        self,
        df: pd.DataFrame,
        interval: str,
        window_size: int,
        source: str,
        z_score_upper: float | Decimal,
        z_score_lower: float | Decimal,
        time_horizon: str,
        entering_trade_condition: str,
    ):
        self.df = df
        self.interval = interval
        self.window_size = window_size
        self.source = source
        self.z_score_upper = z_score_upper
        self.z_score_lower = z_score_lower
        self.time_horizon = time_horizon
        self.entering_trade_condition = entering_trade_condition

        self.standard_deviation_service = StandardDeviationService(
            df=self.df,
            window_size=self.window_size,
            source=self.source,
        )
        self.range_price_service = RangePriceService(
            z_score_upper=self.z_score_upper,
            z_score_lower=self.z_score_lower,
            time_horizon=self.time_horizon,
            interval=self.interval,
        )

    def get_data_by_index(
        self,
        index: datetime | Hashable,
    ) -> Optional[tuple]:
        current_pos = self.df.index.get_loc(index)
        if current_pos == 0:
            return None, None
        previous_index = self.df.index[current_pos - 1]

        sigma = self.standard_deviation_service.get_sigma_by_index(
            index=previous_index,
        )
        if not sigma:
            return None, None

        if self.entering_trade_condition == Strategy.EnteringTradeCondition.OPEN_PRICE.value:
            price = self.df.loc[index, 'open']  # тут возможны разные варианты

        lower_price, upper_price = self.range_price_service.get_values_by_price(
            price=price,
            sigma=sigma,
        )

        if lower_price and upper_price:
            return lower_price, upper_price

        return None, None
