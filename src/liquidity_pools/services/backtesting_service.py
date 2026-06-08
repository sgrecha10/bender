from decimal import Decimal
from typing import Hashable

import pandas as pd

from liquidity_pools.management.commands import backtesting
from liquidity_pools.models import Strategy, LiquidityPoolTick, StrategyPosition
from liquidity_pools.services.pool_strategy_service import PoolStrategyService


class BacktestingService:
    def __init__(
        self,
        strategy_id: int,
    ):
        self.strategy_id = strategy_id
        self.strategy = Strategy.objects.get(pk=strategy_id)
        self.service = PoolStrategyService(strategy_id=self.strategy_id)

        self.df = self.service.get_base_df()

        StrategyPosition.objects.filter(strategy_id=self.strategy_id).delete()

    def run_backtesting(
        self,
    ) -> None:
        """Обходит весь DataFrame, создает/удаляет позиции.

        Предварительно обогощает df аппер/ловер ценой диапаона.
        """
        for index, row in self.df.iterrows():
            #  Определяем, в каком порядке обходим свечу
            if self.strategy.intrabar_price_path == Strategy.IntrabarPricePath.OHLC:
                prices = [row['open'], row['high'], row['low'], row['close']]
            elif self.strategy.intrabar_price_path == Strategy.IntrabarPricePath.OLHC:
                prices = [row['open'], row['low'], row['high'], row['close']]
            else:
                raise ValueError

            for price in prices:
                self.service.make_trade(
                    price=price,
                    index=index,
                    df=self.df,
                )


    def get_backtesting_df(
        self,
    ) -> pd.DataFrame:
        """Возвращает датафрейм для графика."""


        return self.df




    # def add_range_price_to_df(
    #     self,
    #     df: pd.DataFrame,
    # ) -> pd.DataFrame:
    #     """Обогащает df верхней/нижней ценой интервала."""
    #
    #     lower_price_column_name = 'lower_price'
    #     upper_price_column_name = 'upper_price'
    #
    #     df[lower_price_column_name] = None
    #     df[upper_price_column_name] = None
    #
    #     for index, row in df.iterrows():
    #         lower_price, upper_price = self.service.get_range_price_by_index(
    #             index=index,
    #             price=row['open'],  #  ВРЕМЕННОЕ РЕШЕНИЕ
    #             df=df,
    #         )
    #         df.loc[index, lower_price_column_name] = lower_price
    #         df.loc[index, upper_price_column_name] = upper_price
    #
    #     return df




















    # def __init__(
    #     self,
    #     strategy_id: int,
    # ):
    #     self.is_position_open = False  # Есть открытая позиция?
    #     self.strategy_id = strategy_id
    #     self.strategy = Strategy.objects.get(pk=self.strategy_id)
    #
    #     self.strategy_service = PoolStrategyService(
    #         df=df,
    #         interval=self.strategy.interval,
    #         window_size=self.strategy.std_window_size,
    #         source=self.strategy.std_source,
    #         z_score_upper=self.strategy.z_score_upper,
    #         z_score_lower=self.strategy.z_score_lower,
    #         time_horizon=self.strategy.time_horizon,
    #         entering_trade_condition=self.strategy.entering_trade_condition,
    #     )
    #
    #     self.empirical_score = 0
    #
    #
    # def run_backtesting(self):
    #     ohlc_df = self.get_pool_tick_ohlc_df()
    #     strategy_df = self.get_strategy_df(df=ohlc_df)
    #
    #     for index, row in strategy_df.iterrows():
    #         if pd.isna(row['lower_price']) or pd.isna(row['upper_price']):
    #             continue
    #
    #         # код ниже надо перенести в отдельную таску или метод, который будет вызываться с каждым полученным тиком.
    #
    #         # if not self.is_position_open:
    #         #     self._try_open_position(index, row)
    #         # else:
    #         #     self._try_close_position(index, row)
    #         #     self._try_rebalanse_position(index, row)
    #
    #     print('empirical_score', self.empirical_score)
    #
    #     return strategy_df
    #
    #
    # def get_strategy_df(
    #     self,
    #     df: pd.DataFrame,
    # ) -> pd.DataFrame:
    #     """Обогащает df данными из стратегии."""
    #
    #     lower_price_column_name = 'lower_price'
    #     upper_price_column_name = 'upper_price'
    #
    #     df[lower_price_column_name] = None
    #     df[upper_price_column_name] = None
    #
    #     for index, row in df.iterrows():
    #         lower_price, upper_price = strategy_service.get_range_price_by_index(index=index)
    #         df.loc[index, lower_price_column_name] = lower_price
    #         df.loc[index, upper_price_column_name] = upper_price
    #
    #     return df
    #
    # def get_pool_tick_ohlc_df(
    #     self,
    # ) -> pd.DataFrame:
    #     liquidity_pool = self.strategy.liquidity_pool
    #
    #     liquidity_pool_tick_qs = LiquidityPoolTick.objects.filter(
    #         liquidity_pool=liquidity_pool,
    #     ).values(
    #         'block_timestamp',
    #         'tick',
    #     ).order_by('block_timestamp')
    #
    #     df = pd.DataFrame(liquidity_pool_tick_qs)
    #
    #     df['block_timestamp'] = pd.to_datetime(df['block_timestamp'])
    #     df = df.set_index('block_timestamp')
    #
    #     token0_decimal = liquidity_pool.token0.decimals
    #     token1_decimal = liquidity_pool.token1.decimals
    #
    #     df['price'] = (1.0001 ** df['tick']) * 10 ** (token0_decimal - token1_decimal)
    #     candles = df['price'].resample(self.strategy.interval).ohlc()
    #
    #     return candles
    #
    # def _try_open_position(
    #     self,
    #     index: Hashable,
    #     row: pd.Series,
    # ) -> None:
    #     # проверяем ширину диапазона
    #     range_width = row['upper_price'] - row['lower_price']
    #     if self.strategy.maximum_range_width and range_width > self.strategy.maximum_range_width:
    #         return
    #
    #     #  пока только один вариант цены входа - по цене открытия
    #     if self.strategy.entering_trade_condition == Strategy.EnteringTradeCondition.OPEN_PRICE:
    #         self.is_position_open = True
    #         self._log_to_db(index=index, price=row['open'])
    #
    #         # row['open_deal'] = None
    #         # row.loc[index, 'open_deal'] = row['open']
    #         row['open_deal'] = row['open']
    #
    #
    # def _try_close_position(
    #     self,
    #     index: Hashable,
    #     row: pd.Series,
    # ) -> None:
    #     # В каком порядке проверяем?
    #     if self.strategy.closing_trade_condition == Strategy.ClosingTradeCondition.WORSE_ORDER:
    #         if row['lower_price'] > row['low']:
    #             self.is_position_open = False
    #             self._log_to_db(index=index, price=row['lower_price'])
    #             return
    #         if row['upper_price'] < row['high']:
    #             self.is_position_open = False
    #             self._log_to_db(index=index, price=row['upper_price'])
    #             return
    #     else:
    #         if row['upper_price'] < row['high']:
    #             self.is_position_open = False
    #             self._log_to_db(index=index, price=row['upper_price'])
    #             return
    #         if row['lower_price'] > row['low']:
    #             self.is_position_open = False
    #             self._log_to_db(index=index, price=row['lower_price'])
    #             return
    #
    # def _try_rebalanse_position(
    #     self,
    #     index: Hashable,
    #     row: pd.Series,
    # ) -> None:
    #     pass
    #
    # def _log_to_db(
    #     self,
    #     index: Hashable,
    #     price: Decimal,
    # ):
    #     print(index, price, self.is_position_open)
    #
    #     if self.is_position_open:
    #         self.empirical_score -= price
    #     else:
    #         self.empirical_score += price
