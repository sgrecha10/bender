from datetime import datetime
from decimal import Decimal
from typing import Hashable, Optional

import numpy as np
import pandas as pd


class StandardDeviationService:
    CLOSE_TO_CLOSE = 'close_to_close'  # realized volatility
    PARKINSON = 'parkinson'  # Parkinson volatility

    """Стандартное отклонение."""
    def __init__(
        self,
        window_size: int,
        source: str,
    ) -> None:
        self.window_size = window_size
        self.source = source

    def get_sigma_by_index(
        self,
        index: datetime | Hashable,
        df: pd.DataFrame,
    ) -> Optional[float | Decimal]:
        """Возвращает значение sigma (волательность на текущий таймфрейм)
         рассчитанное на переданный index (open_time) включительно

        :param df:
        :param index: datetime
        """
        window_df = df.loc[:index].tail(self.window_size)

        if len(window_df) < self.window_size:
            return

        if self.source == self.CLOSE_TO_CLOSE:
            return self.get_realized_volatility(window_df)
        elif self.source == self.PARKINSON:
            return self.get_parkinson_volatility(window_df)

    def get_parkinson_volatility(
        self,
        window_df: pd.DataFrame,
    ):
        hl = np.log(window_df['high'] / window_df['low'])
        return np.sqrt((hl ** 2).mean() / (4 * np.log(2)))

    def get_realized_volatility(
        self,
        window_df: pd.DataFrame,
    ):
        returns = np.log(window_df['close'] / window_df['close'].shift(1))
        return returns.std()
