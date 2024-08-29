from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
import pandas as pd
import cufflinks as cf
import plotly.offline as plyo
import numpy as np
import plotly.io as pio

from market_data.models import Kline, ExchangeInfo
from django.db.models import F, Q, ExpressionWrapper
from django import forms


class CandleView(View):
    template_name = 'market_data/candle_1.html'

    def get(self, request):
        symbol = request.GET.get('symbol') or 'BTCUSDT'

        df = Kline.objects.filter(symbol_id=symbol).to_dataframe(
            'open_time',
            'open_price',
            'high_price',
            'low_price',
            'close_price',
        )

        df['open_time_hours'] = df['open_time'].dt.strftime("%Y-%m-%d %H")
        df['open_time_days'] = df['open_time'].dt.strftime("%Y-%m-%d")
        df['open_time_months'] = df['open_time'].dt.strftime("%Y-%m")
        df['open_time_years'] = df['open_time'].dt.strftime("%Y")

        # df.index = df['open_time']
        # df.drop(columns=['open_time'], inplace=True)

        df_groupby = df.groupby(['open_time_hours']).agg({
            'open_price': 'first',
            'high_price': 'max',
            'low_price': 'min',
            'close_price': 'last',
        })

        # quotes = df_groupby[['open_price', 'high_price', 'low_price', 'close_price']]
        quotes = df_groupby

        plyo.init_notebook_mode(connected=True)
        cf.go_offline()

        df = cf.QuantFig(
            df=quotes,
            legend='right',
            name=symbol,
            kind='candlestick'
        )

        # df.add_resistance(date='2024-07-29', on='close', color='orange')
        # Adding a support level
        # df.add_support(date='2015-01-28', on='low', color='blue')

        qf = df.iplot(
            asFigure=True,
            theme='white',
            up_color='green',
            down_color='red',
        )
        chart = pio.to_html(qf, include_plotlyjs=False, full_html=False)

        context = {
            'title': 'График',
            'chart': chart,
        }
        return render(request, self.template_name, context=context)
