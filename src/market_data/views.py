from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View
import pandas as pd
import cufflinks as cf
import plotly.offline as plyo
import numpy as np
import plotly.io as pio

from market_data.models import Kline, ExchangeInfo
from django.db.models import F, Q, ExpressionWrapper
from django import forms

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from plotly.express import scatter
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta
import urllib.parse
from .constants import Interval
from indicators.models import MovingAverage


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

        qs = Kline.objects.filter(symbol_id=symbol)
        qs = qs.filter(open_time__gte=start_time) if start_time else qs
        qs = qs.filter(open_time__lte=end_time) if end_time else qs
        qs = qs.group_by_interval(interval)
        df = qs.to_dataframe(index='open_time_group')

        candlestick = go.Candlestick(
            x=df.index,
            open=df['open_price'],
            high=df['high_price'],
            low=df['low_price'],
            close=df['close_price'],
            name=symbol,
        )

        volume = go.Bar(
            x=df.index,
            y=df['volume'],
            name='Volume',
            opacity=0.2,
        )

        # DataFrame for SMA
        sma_df = pd.DataFrame(
            columns=['sma']
        )
        moving_average = MovingAverage.objects.get(id=1)
        for index, row in df.iterrows():
            sma_df.loc[index, 'sma'] = moving_average.get_value_by_index(
                df=df,
                index=index,
            )
        sma = go.Scatter(
            x=sma_df.index,
            y=sma_df['sma'],
            # mode='markers',
            name='SMA',
            marker={
                "color": "blue",
            },
        )

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02)
        fig.add_trace(candlestick, row=2, col=1)
        fig.add_trace(volume, row=1, col=1)
        fig.add_trace(sma, row=2, col=1)

        title = '{interval} ::: {start_time} ... {end_time}'.format(
            interval=Interval(interval).label,
            start_time=start_time.strftime("%d %b %Y %H:%M") if start_time else None,
            end_time=end_time.strftime("%d %b %Y %H:%M") if end_time else None,
        )

        fig.update_layout(
            height=800,
            title=title,
            yaxis_title='Volume',
            xaxis1_rangeslider_visible=False,
            xaxis2_rangeslider_visible=True,
        )

        return pio.to_html(fig, include_plotlyjs=False, full_html=False)




















    # def _get_chart(self, cleaned_data):
    #     symbol = cleaned_data['symbol'].symbol
    #     interval = cleaned_data['interval']
    #     start_time = cleaned_data.get('start_time')
    #     end_time = cleaned_data.get('end_time')
    #
    #     qs = Kline.objects.filter(symbol_id=symbol)
    #     qs = qs.filter(open_time__gte=start_time) if start_time else qs
    #     qs = qs.filter(open_time__lte=end_time) if end_time else qs
    #
    #     df = qs.to_dataframe(
    #         'open_time',
    #         'open_price',
    #         'high_price',
    #         'low_price',
    #         'close_price',
    #         'volume',
    #     )
    #
    #     df['points'] = None
    #
    #     # df.loc[0, 'points'] = 63990
    #     # df.loc[3000, 'points'] = 63000
    #
    #     df['open_time_hours'] = df['open_time'].dt.strftime("%Y-%m-%d %H")
    #     df['open_time_days'] = df['open_time'].dt.strftime("%Y-%m-%d")
    #     df['open_time_months'] = df['open_time'].dt.strftime("%Y-%m")
    #     df['open_time_years'] = df['open_time'].dt.strftime("%Y")
    #
    #     group = self.INTERVAL_MAP[interval.value]
    #
    #     df = df.groupby([group]).agg({
    #         'open_price': 'first',
    #         'high_price': 'max',
    #         'low_price': 'min',
    #         'close_price': 'last',
    #         'volume': 'sum',
    #         'points': 'first',
    #     })
    #
    #     candlestick = go.Candlestick(
    #         x=df.index,
    #         open=df['open_price'],
    #         high=df['high_price'],
    #         low=df['low_price'],
    #         close=df['close_price'],
    #         name=symbol,
    #     )
    #
    #     volume = go.Bar(
    #         x=df.index,
    #         y=df['volume'],
    #         name='Volume',
    #         # marker={
    #         #     "color": "rgba(128,128,128,0.5)",
    #         # },
    #         opacity=0.2,
    #     )
    #
    #     points = go.Scatter(
    #         x=df.index,
    #         y=df['points'],
    #         mode='markers',
    #         name='Points',
    #         marker={
    #             "color": "blue",
    #         },
    #     )
    #
    #     # fig = make_subplots(specs=[[{"secondary_y": True}]])
    #     # fig.add_trace(, secondary_y=True)
    #     # fig.add_trace(volume, secondary_y=False)
    #     # fig.add_trace(points, secondary_y=True)
    #     # fig.layout.yaxis.showgrid = False
    #     # # fig.layout.yaxis2.showgrid = False
    #     # # fig.layout.yaxis1.autoshift = True
    #     # # fig.update_yaxes(autoshift=True)
    #
    #     fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02)
    #     fig.add_trace(candlestick, row=2, col=1)
    #     # fig.add_trace(points, row=2, col=1)
    #     fig.add_trace(volume, row=1, col=1)
    #
    #     title = '{interval} ::: {start_time} ... {end_time}'.format(
    #         interval=interval.codename,
    #         start_time=start_time.strftime("%d %b %Y %H:%M") if start_time else None,
    #         end_time=end_time.strftime("%d %b %Y %H:%M") if end_time else None,
    #     )
    #
    #     fig.update_layout(
    #         height=800,
    #         title=title,
    #         yaxis_title='Volume',
    #         xaxis1_rangeslider_visible=False,
    #         xaxis2_rangeslider_visible=True,
    #         # legend={'bgcolor': 'red'},
    #     )
    #
    #     return pio.to_html(fig, include_plotlyjs=False, full_html=False)

    # def get(self, request, *args, **kwargs):
    #     """Plotly without volume"""
    #     symbol = request.GET.get('symbol') or 'BTCUSDT'
    #     df = Kline.objects.filter(symbol_id=symbol).to_dataframe(
    #         'open_time',
    #         'open_price',
    #         'high_price',
    #         'low_price',
    #         'close_price',
    #         'volume',
    #     )
    #     df['open_time_hours'] = df['open_time'].dt.strftime("%Y-%m-%d %H")
    #     df['open_time_days'] = df['open_time'].dt.strftime("%Y-%m-%d")
    #     df['open_time_months'] = df['open_time'].dt.strftime("%Y-%m")
    #     df['open_time_years'] = df['open_time'].dt.strftime("%Y")
    #
    #     df = df.groupby(['open_time_hours']).agg({
    #         'open_price': 'first',
    #         'high_price': 'max',
    #         'low_price': 'min',
    #         'close_price': 'last',
    #         'volume': 'sum',
    #     })
    #
    #     candlestick = go.Candlestick(
    #         x=df.index,
    #         open=df['open_price'],
    #         high=df['high_price'],
    #         low=df['low_price'],
    #         close=df['close_price'],
    #         showlegend=True,
    #     )
    #
    #     sma = go.Scatter(x=df.index,
    #                      y=df["volume"],
    #                      yaxis="y1",
    #                      name="SMA"
    #                      )
    #
    #     qf = go.Figure(data=[candlestick, sma])
    #
    #     qf.update_layout(
    #         # width=800,
    #         height=800,
    #         title="Apple, March - 2020",
    #         yaxis_title='AAPL Stock'
    #     )
    #
    #     chart = pio.to_html(qf, include_plotlyjs=False, full_html=False)
    #
    #     context = {
    #         'title': 'График',
    #         'chart': chart,
    #     }
    #     return render(request, self.template_name, context=context)


    # def get(self, request):
    #     """cufflinks"""
    #     symbol = request.GET.get('symbol') or 'BTCUSDT'
    #
    #     df = Kline.objects.filter(symbol_id=symbol).to_dataframe(
    #         'open_time',
    #         'open_price',
    #         'high_price',
    #         'low_price',
    #         'close_price',
    #         'volume',
    #     )
    #
    #     df['open_time_hours'] = df['open_time'].dt.strftime("%Y-%m-%d %H")
    #     df['open_time_days'] = df['open_time'].dt.strftime("%Y-%m-%d")
    #     df['open_time_months'] = df['open_time'].dt.strftime("%Y-%m")
    #     df['open_time_years'] = df['open_time'].dt.strftime("%Y")
    #
    #     # df.index = df['open_time']
    #     # df.drop(columns=['open_time'], inplace=True)
    #
    #     df = df.groupby(['open_time_hours']).agg({
    #         'open_price': 'first',
    #         'high_price': 'max',
    #         'low_price': 'min',
    #         'close_price': 'last',
    #         'volume': 'sum',
    #     })
    #
    #     # quotes = df_groupby[['open_price', 'high_price', 'low_price', 'close_price']]
    #     # quotes = df_groupby
    #
    #     plyo.init_notebook_mode(connected=True)
    #
    #     cf.set_config_file(theme='ggplot', sharing='public', offline=True)
    #     # cf.go_offline()
    #
    #     qf = cf.QuantFig(
    #         df=df,
    #         legend='right',
    #         name=symbol,
    #         # kind='candlestick',
    #         down_color='red',
    #         up_color='green',
    #         # theme='solar',  # pearl
    #     )
    #
    #     # qf.add_ema(color='blue')
    #     # qf.add_ema(periods=20, color='green')
    #     # qf.add_bollinger_bands()
    #     # qf.add_volume(colors={'volume': 'green'}, color='blue', up_color='red', down_color='green', column='volume')
    #     # qf.add_volume(up_color='red', down_color='green')
    #     # qf.add_resistance(date='2024-08-29 01', on='close')
    #     # Adding a support level
    #     # df.add_support(date='2015-01-28', on='low', color='blue')
    #
    #     # qf = qf.iplot(asFigure=True, colors={'volume': 'green'}, color='blue', up_color='red', down_color='green',)
    #     qf = qf.iplot(asFigure=True)
    #
    #     # qf = df.iplot(asFigure=True, kind='bar', barmode='stack', colors={
    #     #     'open_time': 'green',
    #     #     'open_price': 'blue',
    #     # })
    #
    #     chart = pio.to_html(qf, include_plotlyjs=False, full_html=False)
    #
    #     context = {
    #         'title': 'График',
    #         'chart': chart,
    #     }
    #     return render(request, self.template_name, context=context)
