from datetime import datetime
from decimal import Decimal
from typing import Hashable, Optional

import pandas as pd
from IPython.core.completer import position_to_cursor

from liquidity_pools.models import (
    Strategy,
    StrategyPosition,
    LiquidityPoolTick,
)
from liquidity_pools.services.range_price_service import RangePriceService
from liquidity_pools.services.standard_deviation_service import StandardDeviationService


class PoolStrategyService:
    def __init__(
        self,
        strategy_id: int,
    ):
        self.strategy_id = strategy_id
        self.strategy = Strategy.objects.get(pk=self.strategy_id)

        self.standard_deviation_service = StandardDeviationService(
            window_size=self.strategy.std_window_size,
            source=self.strategy.std_source,
        )
        self.range_price_service = RangePriceService(
            z_score_upper=self.strategy.z_score_upper,
            z_score_lower=self.strategy.z_score_lower,
            time_horizon=self.strategy.time_horizon,
            interval=self.strategy.interval,
        )

    def get_base_df(self) -> pd.DataFrame:
        """Получить базовый DataFrame ohlc."""
        liquidity_pool = self.strategy.liquidity_pool

        liquidity_pool_tick_qs = LiquidityPoolTick.objects.filter(
            liquidity_pool=liquidity_pool,
        ).values(
            'block_timestamp',
            'tick',
        ).order_by('block_timestamp')

        df = pd.DataFrame(liquidity_pool_tick_qs)

        df['block_timestamp'] = pd.to_datetime(df['block_timestamp'])
        df = df.set_index('block_timestamp')

        token0_decimal = liquidity_pool.token0.decimals
        token1_decimal = liquidity_pool.token1.decimals

        df['price'] = (1.0001 ** df['tick']) * 10 ** (token0_decimal - token1_decimal)

        return df['price'].resample(self.strategy.interval).ohlc()


    def get_range_price_by_index(
        self,
        index: datetime | Hashable,
        price: Decimal,
        df: pd.DataFrame,
    ) -> Optional[tuple]:
        """Возвращает верхнюю/нижнюю цену диапазона."""
        current_pos = df.index.get_loc(index)
        if current_pos == 0:
            return None, None

        previous_index = df.index[current_pos - 1]

        sigma = self.standard_deviation_service.get_sigma_by_index(
            index=previous_index,
            df=df,
        )

        if not sigma:
            return None, None

        lower_price, upper_price = self.range_price_service.get_values_by_price(
            price=price,
            sigma=sigma,
        )

        if lower_price and upper_price:
            return lower_price, upper_price

        return None, None

    def make_trade(
            self,
            price: Decimal,
            index: Hashable,
            df: pd.DataFrame,
    ) -> None:
        """Этот метод вызывается на каждый тик.

        df нужен для получения std & range
        """
        try:
            open_strategy_position = StrategyPosition.objects.get(
                strategy_id=self.strategy.id,
                status=StrategyPosition.StatusChoice.OPEN,
            )
            self.try_close_position(
                position_id=open_strategy_position.id,
                price=price,
                index=index,
                df=df,
            )

        except StrategyPosition.DoesNotExist:
            self.try_open_position(
                price=price,
                index=index,
                df=df,
            )


    def try_open_position(
        self,
        price: Decimal,
        index: Hashable,
        df: pd.DataFrame,
    ) -> str | None:
        """Проверяет условия открытия позиции, открывает если требуется.
        Например, можно проверять now() и входить в позу в определенное время.
        """

        # проверяем, что в текущей свече еще не было закрыто позиций
        # что бы не открывалось больше одной
        try:
            _ = StrategyPosition.objects.get(
                closed_at=index,
                strategy_id=self.strategy.id,
                status__in=[
                    StrategyPosition.StatusChoice.CLOSED_BY_RANGE,
                    StrategyPosition.StatusChoice.CLOSED_MANUAL,
                    StrategyPosition.StatusChoice.CLOSED_FOR_REBALANCING,
                ],
            )
            return
        except StrategyPosition.DoesNotExist:
            pass

        # проверяем, что есть данные по диапазону.
        # для price всегда берем цену открытия. на бою надо будет
        # рассчитывать/кешировать значение на текущий период (день, например)
        lower_price, upper_price = self.get_range_price_by_index(
            index=index,
            price=df.loc[index, 'open'],
            df=df,
        )
        if not lower_price or not upper_price:
            return

        # проверяем ширину диапазона, если требуется.
        if self.strategy.maximum_range_width:
            range_width = upper_price - lower_price
            if range_width > self.strategy.maximum_range_width:
                return

        # получаем цену входа, сейчас единственный вариант
        if self.strategy.entering_trade_condition == Strategy.EnteringTradeCondition.OPEN_PRICE.value:
            entry_price = price
            position = StrategyPosition.objects.create(
                opened_at=index,
                strategy=self.strategy,
                entry_price=entry_price,
                lower_price=lower_price,  # lower_price
                upper_price=upper_price,  # upper_price
            )

            return f'Opened position {position.id}'


    def try_close_position(
        self,
        position_id: int,
        price: Decimal,
        index: Hashable,
        df: pd.DataFrame,
    ):
        position = StrategyPosition.objects.get(id=position_id)

        # проверяем, что цена вышла за пределы диапазона, рассчитанного при входе в позицию.
        exit_price = None
        if price <= position.lower_price:
            exit_price = position.lower_price
        if price >= position.upper_price:
            exit_price = position.upper_price

        if exit_price:
            position.closed_at = index
            position.exit_price = exit_price
            position.status = StrategyPosition.StatusChoice.CLOSED_BY_RANGE
            position.save(update_fields=[
                'closed_at',
                'exit_price',
                'status',
            ])
            return f'Closed position {position.id}'
