import urllib.parse
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from django.shortcuts import render, redirect
from django.views import View
from pandas import DataFrame
from plotly.subplots import make_subplots

from indicators.models import (
    MovingAverage,
    StandardDeviation,
    BollingerBands,
)
from liquidity_pools.models import LiquidityPoolTick
from market_data.models import Kline, ExchangeInfo
from strategies.models import Strategy, StrategyResult
from market_data.constants import Interval
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from market_data.constants import MAP_MINUTE_COUNT
from arbitrations.models import Arbitration, ArbitrationDeal
from django.db.models import Case, Value, When, Q, F, DecimalField
from market_data.constants import AllowedInterval
from copy import copy
import pytz
from liquidity_pools.services.standard_deviation_service import StandardDeviationService
from liquidity_pools.services.pool_strategy_service import PoolStrategyService


class ChartView(View):
    template_name = 'market_data/chart.html'

    interval = Interval.DAY_1.value


    # SEPARATE_ROW_INDICATORS = (
    #     'volume',
    #     'standard_deviations',
    #     # 'moving_averages',
    # )

    def _get_pool_tick_df(self) -> DataFrame:
        data = list(
            LiquidityPoolTick.objects.all()
            .order_by('block_timestamp')
            .values(
                'block_timestamp',
                'tick',
            )
        )

        df = pd.DataFrame(data)

        df['block_timestamp'] = pd.to_datetime(
            df['block_timestamp']
        )

        df = df.set_index(
            'block_timestamp'
        )
        # candles = (
        #     df['tick']
        #     .resample('5min')
        #     .ohlc()
        # )

        df['price'] = (1.0001 ** df['tick']) * 10 ** (18 - 6)

        candles = (
            df['price']
            .resample(self.interval)
            .ohlc()
            # .rename(
            #     columns={
            #         'open': 'open_price',
            #         'high': 'high_price',
            #         'low': 'low_price',
            #         'close': 'close_price',
            #     }
            # )
        )
        return candles

    def get(self, request, *args, **kwargs):
        """Show chart"""
        # df = self._get_kline_df()
        df = self._get_pool_tick_df()

        context = {
            'title': 'some_title',
            'chart': self._get_chart(
                df=df,
                subtitle='Subtitle here',
            ),
            'opts': Kline._meta,
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

        # if volume and 'volume' in self.SEPARATE_ROW_INDICATORS:
        #     row_count += 1
        #     volume_row_number = row_count
        #     row_titles.append('Volume')
        # else:
        #     volume_row_number = 1
        #
        # if standard_deviations and 'standard_deviations' in self.SEPARATE_ROW_INDICATORS:
        #     standard_deviations_count = len(standard_deviations)
        #     standard_deviation_row_number = []
        #     for i in range(standard_deviations_count):
        #         row_count += 1
        #         standard_deviation_row_number.append(row_count)
        #         standard_deviation_codename = StandardDeviation.objects.get(pk=standard_deviations[i]).codename
        #         row_titles.append(standard_deviation_codename)
        # else:
        #     standard_deviations_count = len(standard_deviations)
        #     standard_deviation_row_number = []
        #     for i in range(standard_deviations_count):
        #         standard_deviation_row_number.append(1)
        #
        # if moving_averages and 'moving_averages' in self.SEPARATE_ROW_INDICATORS:
        #     moving_averages_count = len(moving_averages)
        #     moving_averages_row_number = []
        #     for i in range(moving_averages_count):
        #         row_count += 1
        #         moving_averages_row_number.append(row_count)
        #         moving_average_codename = MovingAverage.objects.get(pk=moving_averages[i]).codename
        #         row_titles.append(moving_average_codename)
        # else:
        #     moving_averages_count = len(moving_averages)
        #     moving_averages_row_number = []
        #     for i in range(moving_averages_count):
        #         moving_averages_row_number.append(1)
        #
        # if bollinger_bands and 'bollinger_bands' in self.SEPARATE_ROW_INDICATORS:
        #     row_count += 1
        #     bollinger_bands_row_number = row_count
        #     row_titles.append(bollinger_bands.codename)
        # else:
        #     bollinger_bands_row_number = 1
        #
        # if strategy and 'strategy' in self.SEPARATE_ROW_INDICATORS:
        #     row_count += 1
        #     strategy_row_number = row_count
        #     row_titles.append(strategy.codename)
        # else:
        #     strategy_row_number = 1

        fig = make_subplots(
            rows=row_count, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_titles=row_titles,
            row_heights=self._get_subplots_row_heights(rows=row_count),
            # row_heights=4,
        )
        candlestick_trace = self._get_candlestick_trace(df, subtitle)
        fig.add_trace(candlestick_trace, row=1, col=1)
        fig.add_trace(candlestick_trace, row=2, col=1)

        fig.add_trace(self._get_standard_deviation_trace(df), row=4, col=1)

        strategy_df = self._get_pool_strategy_data(df)
        fig.add_trace(self._get_line_trace(strategy_df, 'lower_price'), row=1, col=1)
        fig.add_trace(self._get_line_trace(strategy_df, 'upper_price'), row=1, col=1)

        # if volume:
        #     fig.add_trace(self._get_volume_trace(df), row=volume_row_number, col=1)

        # if standard_deviation_qs := StandardDeviation.objects.filter(pk__in=standard_deviations):
        #     for i, sd in enumerate(standard_deviation_qs):
        #         fig.add_trace(self._get_standard_deviation_trace(df, sd), row=standard_deviation_row_number[i], col=1)
        #
        # if bollinger_bands:
        #     bollinger_trace_tuple = self._get_bollinger_bands_trace(df, bollinger_bands)
        #     fig.add_trace(bollinger_trace_tuple[0], row=bollinger_bands_row_number, col=1)
        #     fig.add_trace(bollinger_trace_tuple[1], row=bollinger_bands_row_number, col=1)
        #     fig.add_trace(bollinger_trace_tuple[2], row=bollinger_bands_row_number, col=1)
        #
        # if moving_average_qs := MovingAverage.objects.filter(pk__in=moving_averages):
        #     for i, ma in enumerate(moving_average_qs):
        #         fig.add_trace(self._get_moving_average_trace(df, ma), row=moving_averages_row_number[i], col=1)
        #
        # if strategy:
        #     strategy_result_tuple = self._get_strategy_result_trace(df, strategy)
        #     fig.add_trace(strategy_result_tuple[0], row=strategy_row_number, col=1)
        #     fig.add_trace(strategy_result_tuple[1], row=strategy_row_number, col=1)

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
            interval=self.interval,
            window_size=2,
            source=StandardDeviationService.PARKINSON,
            k=1,
            t=1 * 60 * 24,  # 1d
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


        # return go.Scatter(
        #     x=strategy_df.index,
        #     y=strategy_df[upper_price_column_name],
        #     mode='markers',
        #     name=upper_price_column_name,
        #     marker={
        #         # 'color': list(np.random.choice(range(256), size=3)),
        #         'color': 'orange',
        #     },
        # )

    def _get_line_trace(self, df: pd.DataFrame, column_name: str):
        return go.Scatter(
            x=df.index,
            y=df[column_name],
            name=column_name,
        )