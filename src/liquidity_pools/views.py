import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from django.shortcuts import render
from django.views import View
from pandas import DataFrame
from plotly.subplots import make_subplots

from liquidity_pools.models import LiquidityPoolTick, Strategy
from liquidity_pools.services.pool_strategy_service import PoolStrategyService
from liquidity_pools.services.standard_deviation_service import StandardDeviationService


class ChartView(View):
    template_name = 'market_data/chart.html'

    def dispatch(self, request, *args, **kwargs):
        self.strategy = Strategy.objects.get(pk=1)
        return super().dispatch(request, *args, **kwargs)

    def _get_pool_tick_df(
        self,
    ) -> DataFrame:
        liquidity_pool = self.strategy.liquidity_pool

        liquidity_pool_tick_qs = LiquidityPoolTick.objects.filter(
            liquidity_pool=liquidity_pool,
        ).order_by(
            'block_timestamp',
        ).values(
            'block_timestamp',
            'tick',
        )
        df = pd.DataFrame(liquidity_pool_tick_qs)

        df['block_timestamp'] = pd.to_datetime(df['block_timestamp'])
        df = df.set_index('block_timestamp')

        token0_decimal = liquidity_pool.token0.decimals
        token1_decimal = liquidity_pool.token1.decimals

        df['price'] = (1.0001 ** df['tick']) * 10 ** (token0_decimal - token1_decimal)
        candles = df['price'].resample(self.strategy.interval).ohlc()

        return candles

    def get(self, request, *args, **kwargs):
        """Show strategy chart."""
        df = self._get_pool_tick_df()
        context = {
            'title': 'Strategy',
            'chart': self._get_chart(
                df=df,
                subtitle=self.strategy.name,
            ),
            'opts': Strategy._meta,
        }
        return render(request, self.template_name, context=context)

    def _get_chart(
        self,
        df: DataFrame,
        subtitle: str,
    ) -> go.Figure:

        """
        1. Определяем количество необходимых строк. 1 - всегда инструмент, 2, 3 - всегда пустые (для слайдера)
        """
        row_count = 5  # инструмент + невидимый инструмент для слайдера + слайдер
        row_titles = [subtitle, '', '']  # название

        fig = make_subplots(
            rows=row_count, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_titles=row_titles,
            row_heights=self._get_subplots_row_heights(rows=row_count),
        )
        candlestick_trace = self._get_candlestick_trace(df, subtitle)
        fig.add_trace(candlestick_trace, row=1, col=1)
        fig.add_trace(candlestick_trace, row=2, col=1)

        fig.add_trace(self._get_standard_deviation_trace(df), row=4, col=1)

        strategy_df = self._get_pool_strategy_data(df)
        fig.add_trace(self._get_line_trace(strategy_df, 'lower_price'), row=1, col=1)
        fig.add_trace(self._get_line_trace(strategy_df, 'upper_price'), row=1, col=1)

        fig.update_layout(
            # autosize=False,
            # margin=dict(l=50, r=50, t=50, b=100),
            # xaxis=dict(
            #     rangeslider=dict(visible=True),
            #     domain=[1, 0]
            # ),
            height=1000,
            title=subtitle,
            # yaxis_title='Volume',
            xaxis2_rangeslider_thickness=0.1,
            # xaxis_rangeslider_borderwidth=1,
            xaxis_rangeslider_visible=False,
            xaxis2_rangeslider_visible=True,
            yaxis2_visible=False,
            # xaxis2_visible=False,
        )
        # fig.update_xaxes(
        #     rangeslider_yaxis=dict(range=[1, 0])  # Указываем диапазон по оси Y, можно изменить по необходимости
        # )

        return pio.to_html(fig, include_plotlyjs=False, full_html=False)

    def _get_candlestick_trace(self, df: pd.DataFrame, symbol: str):
        return go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=symbol,
        )

    def _get_subplots_row_heights(self, rows: int = 3, slider_thickness: float = 0.1) -> list:
        first_item_map = [0.9, 0.8, 0.7, 0.6]
        prepared_rows = rows - 3

        try:
            first_item_thickness = first_item_map[prepared_rows]
        except IndexError:
            first_item_thickness = 0.5

        row_heights = [first_item_thickness, 0.001, slider_thickness]

        if not prepared_rows:
            return row_heights

        extra_item_thickness = round((1 - first_item_thickness - slider_thickness - 0.001) / prepared_rows, 3)
        return [*row_heights, *[extra_item_thickness for _ in range(prepared_rows)]]

    def _get_standard_deviation_trace(
        self,
        df: pd.DataFrame,
    ):
        standard_deviation_service = StandardDeviationService(
            df=df,
            window_size=3,
            source=StandardDeviationService.PARKINSON,
        )
        column_name = 'std'
        standard_deviation_df = pd.DataFrame(columns=[column_name])
        for index, row in df.iterrows():
            standard_deviation_df.loc[index, column_name] = standard_deviation_service.get_sigma_by_index(
                index=index,
            )

        return go.Scatter(
            x=standard_deviation_df.index,
            y=standard_deviation_df[column_name],
            mode='markers',
            name=column_name,
            marker={
                # 'color': list(np.random.choice(range(256), size=3)),
                'color': 'orange',
            },
        )

    def _get_pool_strategy_data(
        self,
        df: pd.DataFrame,
    ):
        strategy_service = PoolStrategyService(
            df=df,
            interval=self.strategy.interval,
            window_size=self.strategy.std_window_size,
            source=self.strategy.std_source,
            z_score_upper=self.strategy.z_score_upper,
            z_score_lower=self.strategy.z_score_lower,
            time_horizon=self.strategy.time_horizon,
        )

        lower_price_column_name = 'lower_price'
        upper_price_column_name = 'upper_price'
        strategy_df = pd.DataFrame(
            columns=[
                lower_price_column_name,
                upper_price_column_name,
            ]
        )

        for index, row in df.iterrows():
            lower_price, upper_price = strategy_service.get_data_by_index(index=index)

            strategy_df.loc[index, lower_price_column_name] = lower_price
            strategy_df.loc[index, upper_price_column_name] = upper_price

        return strategy_df

    def _get_line_trace(self, df: pd.DataFrame, column_name: str):
        return go.Scatter(
            x=df.index,
            y=df[column_name],
            name=column_name,
        )
