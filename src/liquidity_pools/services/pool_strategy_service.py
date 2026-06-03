from datetime import datetime
from typing import Hashable, Optional

import pandas as pd

from liquidity_pools.services.range_price_service import RangePriceService
from liquidity_pools.services.standard_deviation_service import StandardDeviationService


class PoolStrategyService:
    def __init__(
        self,
        df: pd.DataFrame,
        interval: str,
        window_size: int,
        source: str,
        k: int,
        t: int,
    ):
        self.df = df
        self.interval = interval
        self.window_size = window_size
        self.source = source
        self.k = k  # надо придумать две разные k, вверх и вниз
        self.t = t

        self.standard_deviation_service = StandardDeviationService(
            df=self.df,
            window_size=self.window_size,
            source=self.source,
        )
        self.range_price_service = RangePriceService(
            k=self.k,
            t=self.t,
            interval=self.interval,
        )

    def get_data_by_index(
        self,
        index: datetime | Hashable,
    ) -> Optional[tuple]:
        current_pos = self.df.index.get_loc(index)
        previous_index = self.df.index[current_pos - 1]

        sigma = self.standard_deviation_service.get_sigma_by_index(
            index=previous_index,
        )
        if not sigma:
            return None, None

        price = self.df.loc[index, 'open']  # тут возможны разные варианты

        lower_price, upper_price = self.range_price_service.get_values_by_price(
            price=price,
            sigma=sigma,
        )

        if lower_price and upper_price:
            return lower_price, upper_price

        return None, None
