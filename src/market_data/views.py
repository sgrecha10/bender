import urllib.parse

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from django.shortcuts import render, redirect
from django.views import View
from plotly.subplots import make_subplots

from indicators.models import MovingAverage, StandardDeviation
from market_data.models import Kline, ExchangeInfo
from .constants import Interval
from strategies.models import Strategy, StrategyResult


class ChartView(View):
    template_name = 'market_data/chart.html'

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
        }

        if form.is_valid():
            cleaned_data = form.cleaned_data
            context['title'] = cleaned_data['symbol'].symbol
            context['chart'] = self._get_chart(cleaned_data)

        return render(request, self.template_name, context=context)

    def _get_default_data_url(self):
        default_data = {
            'symbol': ExchangeInfo.objects.get(
                pk=Kline.objects.values_list('symbol', flat=True).first()),
            'interval': Interval.MONTH_1.value,
        }
        return self.request.path + '?' + urllib.parse.urlencode(default_data)

    def _get_chart(self, cleaned_data):
        symbol = cleaned_data['symbol'].symbol
        interval = cleaned_data['interval']
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        volume = cleaned_data.get('volume')
        moving_averages = [item.pk for item in cleaned_data.get('moving_averages', [])]
        strategy = cleaned_data.get('strategy')
        standard_deviation = cleaned_data.get('standard_deviation')

        qs = Kline.objects.filter(symbol_id=symbol)
        qs = qs.filter(open_time__gte=start_time) if start_time else qs
        qs = qs.filter(open_time__lte=end_time) if end_time else qs
        qs = qs.group_by_interval(interval)
        df = qs.to_dataframe(index='open_time_group')

        rows = 1
        row_heights = [1]
        if volume:
            rows += 1

        if standard_deviation:
            rows += 1

        if rows == 2:
            row_heights = [0.8, 0.2]
        elif rows == 3:
            row_heights = [0.6, 0.2, 0.2]

        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.2,
            row_heights=row_heights,
        )
        fig.add_trace(self._get_candlestick_trace(df, symbol), row=1, col=1)

        if volume:
            fig.add_trace(self._get_volume_trace(df), row=2, col=1)
        if standard_deviation:
            row = 2
            if rows == 3:
                row = 3
            fig.add_trace(self._get_standard_deviation_trace(df, standard_deviation), row=row, col=1)

        # полосы боллинджера по быстрому
        fig.add_trace(self._get_bollindger_trace_1(df, standard_deviation), row=1, col=1)
        fig.add_trace(self._get_bollindger_trace_2(df, standard_deviation), row=1, col=1)

        if moving_average_qs := MovingAverage.objects.filter(pk__in=moving_averages):
            for ma in moving_average_qs:
                fig.add_trace(self._get_moving_average_trace(df, ma), row=1, col=1)

        if strategy:
            fig.add_trace(self._get_strategy_result_trace(df, strategy), row=1, col=1)

        title = '{interval} ::: {start_time} ... {end_time}'.format(
            interval=Interval(interval).label,
            start_time=start_time.strftime("%d %b %Y %H:%M") if start_time else None,
            end_time=end_time.strftime("%d %b %Y %H:%M") if end_time else None,
        )

        fig.update_layout(
            height=1000,
            title=title,
            # yaxis_title='Volume',
            # xaxis1_rangeslider_visible=True,
            # xaxis2_rangeslider_visible=True,  # True
        )

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

    def _get_strategy_result_trace(self, df: pd.DataFrame, strategy: Strategy):
        strategy_result_qs = StrategyResult.objects.filter(
            strategy=strategy,
            kline__open_time__gte=df.iloc[0].name,
            kline__open_time__lte=df.iloc[-1].name,
        ).values_list('kline__open_time', 'price')

        df = pd.DataFrame(
            data=strategy_result_qs,
            columns=['open_time', 'price'],
        )
        df.set_index('open_time', inplace=True, drop=True)
        df.sort_index(inplace=True)

        return go.Scatter(
            x=df.index,
            y=df['price'],
            mode='markers',
            name=strategy.name,
            marker={
                # 'color': list(np.random.choice(range(256), size=3)),
                'color': 'orange',
            },
        )

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

    def _get_bollindger_trace_1(self, df: pd.DataFrame, standard_deviation: StandardDeviation):
        source_df = standard_deviation.moving_average.get_source_df(base_df=df)

        bollindger_df = pd.DataFrame(
            columns=['b_1', 'b_2']
        )
        for index, row in df.iterrows():
            bollindger_df.loc[index, 'b_1'] = standard_deviation.moving_average.get_value_by_index(
                index=index,
                source_df=source_df,
            ) + standard_deviation.get_value_by_index(
                index=index,
                source_df=source_df,
            ) * 2

        return go.Scatter(
            x=bollindger_df.index,
            y=bollindger_df['b_1'],
            # mode='markers',
            name='b_1',
            marker={
                # 'color': list(np.random.choice(range(256), size=3)),
                'color': 'green',
            },
        )

    def _get_bollindger_trace_2(self, df: pd.DataFrame, standard_deviation: StandardDeviation):
        source_df = standard_deviation.moving_average.get_source_df(base_df=df)

        bollindger_df = pd.DataFrame(
            columns=['b_1', 'b_2']
        )
        for index, row in df.iterrows():
            bollindger_df.loc[index, 'b_2'] = standard_deviation.moving_average.get_value_by_index(
                index=index,
                source_df=source_df,
            ) - standard_deviation.get_value_by_index(
                index=index,
                source_df=source_df,
            ) * 2

        return go.Scatter(
            x=bollindger_df.index,
            y=bollindger_df['b_2'],
            # mode='markers',
            name='b_2',
            marker={
                # 'color': list(np.random.choice(range(256), size=3)),
                'color': 'green',
            },
        )
