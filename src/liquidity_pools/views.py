import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from django.shortcuts import render
from django.views import View
from pandas import DataFrame
from plotly.subplots import make_subplots

from liquidity_pools.models import Strategy
from liquidity_pools.services.backtesting_service import BacktestingService


class ChartView(View):
    template_name = 'liquidity_pools/chart.html'

    def get(self, request, *args, **kwargs):
        """Show strategy chart."""
        strategy_id = request.GET.get('strategy_id')
        service = BacktestingService(strategy_id=strategy_id)

        service.run_backtesting()  # запускаем и пересчитываем при каждом отображении

        df = service.get_backtesting_df()

        context = {
            'title': 'Strategy',
            'chart': self._get_chart(
                df=df,
                subtitle=service.strategy.name,
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
        row_count = 4  # инструмент + невидимый инструмент для слайдера + слайдер
        row_titles = [subtitle, '', '']  # название

        fig = make_subplots(
            rows=row_count, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_titles=row_titles,
            row_heights=[0.7, 0.001, 0.15, 0.15],
        )
        candlestick_trace = self._get_candlestick_trace(df, subtitle)
        fig.add_trace(candlestick_trace, row=1, col=1)
        fig.add_trace(candlestick_trace, row=2, col=1)

        if 'lower_price' in df.columns and 'upper_price' in df.columns:
            fig.add_trace(self._get_line_trace(df, 'lower_price'), row=1, col=1)
            fig.add_trace(self._get_line_trace(df, 'upper_price'), row=1, col=1)

        if 'range_width' in df.columns:
            fig.add_trace(self._get_bar_trace(df, 'range_width'), row=4, col=1)

        if 'entry_price' in df.columns:
            fig.add_trace(self._get_position_entry_price_trace(df), row=1, col=1)

        if 'exit_price' in df.columns:
            fig.add_trace(self._get_position_exit_price_trace(df), row=1, col=1)

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

    def _get_line_trace(self, df: pd.DataFrame, column_name: str):
        return go.Scatter(
            x=df.index,
            y=df[column_name],
            name=column_name,
        )

    def _get_bar_trace(self, df: pd.DataFrame, column_name: str):
        return go.Bar(
            x=df.index,
            y=df[column_name],
            name=column_name,
            marker={
                'color': 'orange',
            },
        )

    def _get_position_entry_price_trace(self, df: pd.DataFrame):
        return go.Scatter(
            x=df.index,
            y=df['entry_price'],
            mode='markers+text',  # markers+text
            marker={
                'color': 'green',   # green, orange
                'symbol': 'triangle-up',  # triangle-down, triangle-up, diamond
                'size': 11,
            },
            # text=df['entry_price'],
            # textposition='top center',
        )

    def _get_position_exit_price_trace(self, df: pd.DataFrame):
        return go.Scatter(
            x=df.index,
            y=df['exit_price'],
            mode='markers+text',
            marker={
                'color': 'red',   # green, orange
                'symbol': 'triangle-down',  # triangle-down, triangle-up, diamond
                'size': 11,
            },
            # text=df['exit_price'],
            # textposition='top center',
        )
