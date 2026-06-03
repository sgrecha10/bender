from decimal import Decimal

import numpy as np

from liquidity_pools.constants import MAP_MINUTE_COUNT


class RangePriceService:
    def __init__(
        self,
        z_score_upper: float | Decimal,
        z_score_lower: float | Decimal,
        time_horizon: str,
        interval: str,
    ):
        # k = 1 → ~68% вероятности остаться в диапазоне;
        # k = 2 → ~95%;
        # k = 3 → ~99.7%.
        self.z_score_upper = float(z_score_upper)
        self.z_score_lower = float(z_score_lower)
        self.time_horizon = time_horizon
        self.interval = interval

    def get_values_by_price(
        self,
        price: float | Decimal,
        sigma: float | Decimal,
    ) -> tuple:
        """Возвращает upper_price/lower_price рассчитанные для переданной цены и сигмы.
        Сигма должна быть в размерности текущего таймфрейма.
        """
        interval_minutes = MAP_MINUTE_COUNT[self.interval]
        periods_per_year = 365 * 24 * 60 / interval_minutes
        sigma_annual = sigma * np.sqrt(periods_per_year)

        t_annual = MAP_MINUTE_COUNT[self.time_horizon] / (365 * 24 * 60)

        upper = price * np.exp(self.z_score_upper * sigma_annual * np.sqrt(t_annual))
        lower = price * np.exp(-self.z_score_lower * sigma_annual * np.sqrt(t_annual))

        return lower, upper

        """
        sigma_5m = 111  #  5 минутная сигма (у меня дневная)

        periods_per_year = (
                365 * 24 * 60 / 5
        )

        # значит, если сигма дневная, то periods_per_year = 365
        # sigma_annual = sigma_1d * np.sqrt(365)
        sigma_1d = 0.01318842
        sigma_annual = sigma_1d * np.sqrt(365)  # 0.2519644103146037
        # sigma_annual = sigma_5m * np.sqrt(periods_per_year)  # годовая сигма

        price = 2334.178  # текущая цена (взял цену закрытия текущей свечи, но вооще это цена когда позу отрываешь)
        # k = 1 → ~68% вероятности остаться в диапазоне;
        # k = 2 → ~95%;
        # k = 3 → ~99.7%.
        k = 1
        sigma = sigma_annual
        T = 7 / 365  # Это горизонт времени в тех же единицах, что и sigma. это горизон времени 7 дней.
        T = 1/ 365  # возьмем горизонт на сутки.

        upper = price * np.exp(k * sigma * np.sqrt(T))  # 2365.1660121226496

        lower = price * np.exp(-k * sigma * np.sqrt(T))  # 2303.5959876635775


        #  Сейчас тоже самое, но не пересчитывая в годовую сигму ТОЖЕ САМОЕ.
        sigma_1d = 0.01318842
        price = 2334.178
        k = 1
        T = 1
        sigma = sigma_1d
        upper = price * np.exp(k * sigma * np.sqrt(T))  # 2365.1660121226496
        lower = price * np.exp(-k * sigma * np.sqrt(T))  # 2303.5959876635775
        """
