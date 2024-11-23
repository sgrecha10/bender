import urllib.parse
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from django.shortcuts import render, redirect
from django.views import View
from plotly.subplots import make_subplots

from indicators.models import (
    MovingAverage,
    StandardDeviation,
    BollingerBands,
)
from market_data.models import Kline, ExchangeInfo
from strategies.models import Strategy, StrategyResult
from .constants import Interval


class ChartView(View):
    template_name = 'market_data/chart.html'

    SEPARATE_ROW_INDICATORS = (
        'volume',
        'standard_deviations',
        # 'moving_averages',
    )

    def get(self, request, *args, **kwargs):
        """Show chart"""
        from .forms import ChartForm

        data = request.GET
        if not data:
            return redirect(self._get_default_data_url())

        form = ChartForm(data=data)
        context = {
            'title': None,
            'chart': None,
            'form': form,
            'opts': Kline._meta,
            'strategy': self._get_strategy_result(data=data),
        }

        if form.is_valid():
            cleaned_data = form.cleaned_data
            context['title'] = cleaned_data['symbol'].symbol
            context['chart'] = self._get_chart(cleaned_data)

        return render(request, self.template_name, context=context)

    def _get_strategy_result(self, data: dict) -> Optional[dict]:
        """ Результат стратегии в чарт """

        if data.get('strategy'):
            strategy_result_qs = StrategyResult.objects.filter(strategy_id=data['strategy'])

            strategy_result_points = 0
            for item in strategy_result_qs:
                buy = item.buy
                sell = item.sell
                if buy:
                    strategy_result_points -= buy
                elif sell:
                    strategy_result_points += sell

            first_item = strategy_result_qs.first()
            last_item = strategy_result_qs.last()
            first_deal_price = first_item.buy or first_item.sell
            strategy_result_percent = (((first_deal_price + strategy_result_points) / first_deal_price) - 1) * 100

            price_change_points = last_item.kline.close_price - first_item.kline.open_price
            price_change_percent = ((last_item.kline.close_price / first_item.kline.open_price) - 1) * 100

            strategy_efficiency = ((strategy_result_points / price_change_points) - 1) * 100

            total_deals = strategy_result_qs.filter(state=StrategyResult.State.OPEN).count()
            successful_deals = strategy_result_qs.filter(state=StrategyResult.State.PROFIT).count()
            winrate = (successful_deals / total_deals) * 100

            return {
                'strategy_codename': first_item.strategy.get_codename_display(),
                'strategy_range': f'{first_item.strategy.start_time} <br> {first_item.strategy.end_time}',
                'strategy_result_percent': strategy_result_percent,
                'strategy_result_points': strategy_result_points,
                'strategy_efficiency': strategy_efficiency,
                'price_change_percent': price_change_percent,
                'price_change_points': price_change_points,
                'total_deals': total_deals,
                'successful_deals': successful_deals,
                'winrate': winrate,
            }

    def _get_default_data_url(self):
        default_data = {
            'symbol': ExchangeInfo.objects.get(
                pk=Kline.objects.values_list('symbol', flat=True).first()),
            'interval': Interval.MONTH_1.value,
        }
        return self.request.path + '?' + urllib.parse.urlencode(default_data)

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

    def _get_chart(self, cleaned_data):
        symbol = cleaned_data['symbol'].symbol
        interval = cleaned_data['interval']
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        volume = cleaned_data.get('volume')
        strategy = cleaned_data.get('strategy')
        bollinger_bands = cleaned_data.get('bollinger_bands')

        moving_averages = [item.pk for item in cleaned_data.get('moving_averages', [])]
        standard_deviations = [item.pk for item in cleaned_data.get('standard_deviations', [])]

        qs = Kline.objects.filter(symbol_id=symbol)
        qs = qs.filter(open_time__gte=start_time) if start_time else qs
        qs = qs.filter(open_time__lte=end_time) if end_time else qs
        qs = qs.group_by_interval(interval)
        df = qs.to_dataframe(index='open_time_group')

        """
        1. Определяем количество необходимых строк. 1 - всегда инструмент, 2, 3 - всегда пустые (для слайдера)
        """
        row_count = 3  # инструмент + невидимый инструмент для слайдера + слайдер
        row_titles = [symbol, '', '']  # название

        if volume and 'volume' in self.SEPARATE_ROW_INDICATORS:
            row_count += 1
            volume_row_number = row_count
            row_titles.append('Volume')
        else:
            volume_row_number = 1

        if standard_deviations and 'standard_deviations' in self.SEPARATE_ROW_INDICATORS:
            standard_deviations_count = len(standard_deviations)
            standard_deviation_row_number = []
            for i in range(standard_deviations_count):
                row_count += 1
                standard_deviation_row_number.append(row_count)
                standard_deviation_codename = StandardDeviation.objects.get(pk=standard_deviations[i]).codename
                row_titles.append(standard_deviation_codename)
        else:
            standard_deviations_count = len(standard_deviations)
            standard_deviation_row_number = []
            for i in range(standard_deviations_count):
                standard_deviation_row_number.append(1)

        if moving_averages and 'moving_averages' in self.SEPARATE_ROW_INDICATORS:
            moving_averages_count = len(moving_averages)
            moving_averages_row_number = []
            for i in range(moving_averages_count):
                row_count += 1
                moving_averages_row_number.append(row_count)
                moving_average_codename = MovingAverage.objects.get(pk=moving_averages[i]).codename
                row_titles.append(moving_average_codename)
        else:
            moving_averages_count = len(moving_averages)
            moving_averages_row_number = []
            for i in range(moving_averages_count):
                moving_averages_row_number.append(1)

        if bollinger_bands and 'bollinger_bands' in self.SEPARATE_ROW_INDICATORS:
            row_count += 1
            bollinger_bands_row_number = row_count
            row_titles.append(bollinger_bands.codename)
        else:
            bollinger_bands_row_number = 1

        if strategy and 'strategy' in self.SEPARATE_ROW_INDICATORS:
            row_count += 1
            strategy_row_number = row_count
            row_titles.append(strategy.codename)
        else:
            strategy_row_number = 1

        fig = make_subplots(
            rows=row_count, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_titles=row_titles,
            row_heights=self._get_subplots_row_heights(rows=row_count),
        )
        candlestick_trace = self._get_candlestick_trace(df, symbol)
        fig.add_trace(candlestick_trace, row=1, col=1)
        fig.add_trace(candlestick_trace, row=2, col=1)

        if volume:
            fig.add_trace(self._get_volume_trace(df), row=volume_row_number, col=1)

        if standard_deviation_qs := StandardDeviation.objects.filter(pk__in=standard_deviations):
            for i, sd in enumerate(standard_deviation_qs):
                fig.add_trace(self._get_standard_deviation_trace(df, sd), row=standard_deviation_row_number[i], col=1)

        if bollinger_bands:
            bollinger_trace_tuple = self._get_bollinger_bands_trace(df, bollinger_bands)
            fig.add_trace(bollinger_trace_tuple[0], row=bollinger_bands_row_number, col=1)
            fig.add_trace(bollinger_trace_tuple[1], row=bollinger_bands_row_number, col=1)
            fig.add_trace(bollinger_trace_tuple[2], row=bollinger_bands_row_number, col=1)

        if moving_average_qs := MovingAverage.objects.filter(pk__in=moving_averages):
            for i, ma in enumerate(moving_average_qs):
                fig.add_trace(self._get_moving_average_trace(df, ma), row=moving_averages_row_number[i], col=1)

        if strategy:
            strategy_result_tuple = self._get_strategy_result_trace(df, strategy)
            fig.add_trace(strategy_result_tuple[0], row=strategy_row_number, col=1)
            fig.add_trace(strategy_result_tuple[1], row=strategy_row_number, col=1)

        title = '{interval} ::: {start_time} ... {end_time}'.format(
            interval=Interval(interval).label,
            start_time=start_time.strftime("%d %b %Y %H:%M") if start_time else None,
            end_time=end_time.strftime("%d %b %Y %H:%M") if end_time else None,
        )

        fig.update_layout(
            # autosize=False,
            # margin=dict(l=50, r=50, t=50, b=100),
            # xaxis=dict(
            #     rangeslider=dict(visible=True),
            #     domain=[1, 0]
            # ),
            height=1000,
            title=title,
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
            open=df['open_price'],
            high=df['high_price'],
            low=df['low_price'],
            close=df['close_price'],
            name=symbol,
        )

    def _get_volume_trace(self, df: pd.DataFrame):
        return go.Bar(
            x=df.index,
            y=df['volume'],
            name='Volume',
            opacity=0.2,
        )

    def _get_moving_average_trace(self, df: pd.DataFrame, moving_average: MovingAverage):
        column_name = f'ma_{moving_average.id}'
        source_df = moving_average.get_source_df(base_df=df)

        moving_average_df = pd.DataFrame(
            columns=[column_name]
        )
        for index, row in df.iterrows():
            moving_average_df.loc[index, column_name] = moving_average.get_value_by_index(
                index=index,
                source_df=source_df,
            )
        return go.Scatter(
            x=moving_average_df.index,
            y=moving_average_df[column_name],
            # mode='markers',
            name=moving_average.codename,
            marker={
                'color': list(np.random.choice(range(256), size=3)),
            },
        )

    def _get_strategy_result_trace(self, df: pd.DataFrame, strategy: Strategy) -> tuple:
        strategy_result_qs = StrategyResult.objects.filter(
            strategy=strategy,
            kline__open_time__gte=df.iloc[0].name,
            kline__open_time__lte=df.iloc[-1].name,
        ).values_list('kline__open_time', 'buy', 'sell', 'state')

        df = pd.DataFrame(
            data=strategy_result_qs,
            columns=['open_time', 'buy', 'sell', 'state'],
        )
        df.set_index('open_time', inplace=True, drop=True)
        df.sort_index(inplace=True)

        buy_trace = go.Scatter(
            x=df.index,
            y=df['buy'],
            mode='markers+text',
            # name=strategy.name,
            marker={
                # 'color': list(np.random.choice(range(256), size=3)),
                'color': 'green',
                'symbol': 'triangle-up',  # triangle-down, triangle-up
                'size': 13,
            },
            text=df['state'],
            textposition='top center',
        )
        sell_trace = go.Scatter(
            x=df.index,
            y=df['sell'],
            mode='markers+text',
            # mode='markers',
            # name=strategy.name,
            marker={
                'color': 'red',
                'symbol': 'triangle-down',  # triangle-down, triangle-up
                'size': 13,
            },
            text=df['state'],
            textposition='top center',
            textfont=dict(
                family='Arial',
                size=14,
                color='blue',
            ),
        )
        return buy_trace, sell_trace

    def _get_standard_deviation_trace(self, df: pd.DataFrame, standard_deviation: StandardDeviation):
        column_name = f'sd_{standard_deviation.id}'
        source_df = standard_deviation.moving_average.get_source_df(base_df=df)

        standard_deviation_df = pd.DataFrame(
            columns=[column_name]
        )
        for index, row in df.iterrows():
            standard_deviation_df.loc[index, column_name] = standard_deviation.get_value_by_index(
                index=index,
                source_df=source_df,
            )
        return go.Scatter(
            x=standard_deviation_df.index,
            y=standard_deviation_df[column_name],
            mode='markers',
            name=standard_deviation.codename,
            marker={
                # 'color': list(np.random.choice(range(256), size=3)),
                'color': 'orange',
            },
        )

    def _get_bollinger_bands_trace(self, df: pd.DataFrame, bollinger_bands: BollingerBands) -> Optional[tuple]:
        source_df = bollinger_bands.moving_average.get_source_df(base_df=df)

        bollinger_df = pd.DataFrame(
            columns=['b_0', 'b_1', 'b_2']
        )
        for index, row in df.iterrows():
            result = bollinger_bands.get_values_by_index(
                index=index,
                source_df=source_df,
            )

            bollinger_df.loc[index, 'b_0'] = result[0]
            bollinger_df.loc[index, 'b_1'] = result[1]
            bollinger_df.loc[index, 'b_2'] = result[2]

        b_0 = go.Scatter(
            x=bollinger_df.index,
            y=bollinger_df['b_0'],
            # mode='markers',
            name='b_0',
        )
        b_1 = go.Scatter(
            x=bollinger_df.index,
            y=bollinger_df['b_1'],
            # mode='markers',
            name='b_1',
        )
        b_2 = go.Scatter(
            x=bollinger_df.index,
            y=bollinger_df['b_2'],
            # mode='markers',
            name='b_2',
        )
        return b_0, b_1, b_2
