import pandas as pd
from django.db.models import Sum, F, DecimalField, Avg, ExpressionWrapper, Value, Case, When, Count

from liquidity_pools.models import Strategy, StrategyPosition, LiquidityPoolTick
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

    def run_backtesting(
        self,
    ) -> None:
        """Обходит весь DataFrame, создает/удаляет позиции.

        Предварительно обогощает df аппер/ловер ценой диапаона.
        """
        StrategyPosition.objects.filter(strategy_id=self.strategy_id).delete()

        filters = {}
        if self.strategy.block_timestamp_start:
            filters["block_timestamp__gte"] = self.strategy.block_timestamp_start
        if self.strategy.block_timestamp_end:
            filters["block_timestamp__lte"] = self.strategy.block_timestamp_end

        liquidity_pool_tick_qs = LiquidityPoolTick.objects.filter(
            liquidity_pool=self.strategy.liquidity_pool,
            **filters
        ).values(
            'block_timestamp',
            'tick',
        ).order_by('block_timestamp')

        token0_decimal = self.strategy.liquidity_pool.token0.decimals
        token1_decimal = self.strategy.liquidity_pool.token1.decimals

        for row in liquidity_pool_tick_qs:
            timestamp = row['block_timestamp']
            tick = row['tick']
            price = (1.0001 ** tick) * 10 ** (token0_decimal - token1_decimal)

            print(timestamp, tick, price)

            self.service.make_trade(
                price=price,
                df=self.df,
                index=timestamp,
            )

        # ниже расчет результата бектестинга
        self.backtesting_result()

    def get_rich_ohlc_df(self) -> pd.DataFrame:
        """Возвращает свечи с выбранным interval, и range_prices, price_width."""
        lower_price_column_name = 'lower_price'
        upper_price_column_name = 'upper_price'
        range_width_column_name = 'range_width'

        self.df[lower_price_column_name] = None
        self.df[upper_price_column_name] = None
        self.df[range_width_column_name] = None

        for index, row in self.df.iterrows():
            lower_price, upper_price = self.service.get_range_price_by_index(
                index=index,
                price=row['open'],
                df=self.df,
            )
            if not lower_price and not upper_price:
                continue

            self.df.loc[index, lower_price_column_name] = lower_price
            self.df.loc[index, upper_price_column_name] = upper_price
            self.df.loc[index, range_width_column_name] = upper_price - lower_price

        return self.df

    def get_backtesting_df(
        self,
    ) -> pd.DataFrame:
        """Возвращает датафрейм c точками входа/выхода."""
        strategy_position_qs = StrategyPosition.objects.filter(strategy_id=self.strategy_id)

        df = pd.DataFrame(columns=['entry_price', 'exit_price'])
        df.index = pd.to_datetime(df.index, utc=True)

        for row in strategy_position_qs:
            if row.opened_at:
                index = row.opened_at
                df.loc[index, 'entry_price'] = row.entry_price

            if row.closed_at:
                index = row.closed_at
                df.loc[index, 'exit_price'] = row.exit_price

        return df

    def backtesting_result(self):
        strategy_position = StrategyPosition.objects.filter(
            strategy_id=self.strategy_id,
        ).exclude(
            status=StrategyPosition.StatusChoice.OPEN,
        ).aggregate(
            pnl_absolute=Sum(
                F('exit_price') - F('entry_price'),
                output_field=DecimalField(
                    max_digits=30,
                    decimal_places=18,
                ),
            ),
            pnl_percent=Avg(
                ExpressionWrapper(
                    F('exit_price') / F('entry_price') - Value(1),
                    output_field=DecimalField(
                        max_digits=30,
                        decimal_places=18,
                    ),
                ),
            ),
            win_rate=Avg(
                Case(
                    When(
                        exit_price__gt=F('entry_price'),
                        then=Value(1),
                    ),
                    default=Value(0),
                )
            ),
            positions_count=Count('id'),
        )

        print('==========================================================================')
        print('strategy.name', self.strategy.name)
        print('pnl_absolute', strategy_position['pnl_absolute'])
        print('pnl_percent', strategy_position['pnl_percent'] and round(strategy_position['pnl_percent'] * 100, 3))
        print('win_rate', strategy_position['win_rate'] and round(strategy_position['win_rate'] * 100, 2))
        print('positions_count', strategy_position['positions_count'])
        print('==========================================================================')
