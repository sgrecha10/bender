from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from django.db import models
from pandas import DataFrame

from core.utils.db_utils import BaseModel
from market_data.constants import AllowedInterval, Interval
from market_data.models import ExchangeInfo, Kline
from strategies.models import Strategy


class MovingAverage(BaseModel):
    class Type(models.TextChoices):
        SMA = 'sma', 'SMA'
        EMA = 'ema', 'EMA'

    class DataSource(models.TextChoices):
        OPEN = 'open', 'Open price'
        CLOSE = 'close', 'Close price'
        HIGH = 'high', 'High price'
        LOW = 'low', 'Low price'
        HIGH_LOW = 'high_low', 'High-Low average'
        OPEN_CLOSE = 'open_close', 'Open-Close average'

    codename = models.CharField(
        verbose_name='Codename',
        max_length=255,
        unique=True,
    )
    description = models.TextField(
        verbose_name='Description',
        blank=True, default='',
    )
    data_source = models.CharField(
        verbose_name='Data source',
        max_length=20,
        choices=DataSource.choices,
    )
    type = models.CharField(
        verbose_name='Type',
        max_length=20,
        choices=Type.choices,
    )
    kline_count = models.IntegerField(
        verbose_name='K-Line Count',
        help_text='Количество свечей для расчета',
    )
    factor_alfa = models.DecimalField(
        verbose_name='Factor Alfa',
        help_text='Используется для расчета EMA',
        max_digits=5,
        decimal_places=4,
        default=0,
    )
    factor_alfa_auto = models.BooleanField(
        verbose_name='Factor Alfa Auto',
        help_text='Используется для расчета EMA',
        default=False,
    )
    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.SET_NULL,
        verbose_name='Strategy',
        null=True, blank=True,
    )
    symbol = models.ForeignKey(
        ExchangeInfo,
        on_delete=models.CASCADE,
        verbose_name='Symbol',
    )
    interval = models.CharField(
        verbose_name='Interval',
        choices=AllowedInterval.choices,
        max_length=10,
    )

    class Meta:
        verbose_name = 'MovingAverage'
        verbose_name_plural = 'MovingAverage'

    def __str__(self):
        return (
            f'{self.id} '
            f'- {self.codename} '
            f'- {self.get_type_display()} '
            f'- {self.kline_count} '
            f'- {self.get_data_source_display()} '
            f'- {self.symbol} '
            f'- {self.get_interval_display()} '
        )

    def get_source_df(self, **kwargs) -> DataFrame:
        """Возвращает source DataFrame"""
        qs = Kline.objects.filter(symbol_id=self.symbol, **kwargs)
        qs = qs.group_by_interval(self.interval)
        return qs.to_dataframe(index='open_time_group')

    def get_value_by_index(self,
                           index: datetime,
                           source_df: DataFrame = None,
                           self_creation_df: bool = False) -> Optional[Decimal]:
        """Возвращает значение MA рассчитанное на переданный index (open_time) включительно

        :param index: datetime
        :param source_df: DataFrame
        :param self_creation_df: True - не требует source_df

        1. Если index не найден в source_df - return None
        2. Если количество свечей для расчета в source_df меньше self.kline_count - return None
        """
        if self_creation_df:
            # Генерируем source_df если self_creation_df = True
            map_minute_count = {
                Interval.HOUR_1: 60,
                Interval.DAY_1: 60*24,
                Interval.WEEK_1: 60*24*7,
                Interval.MONTH_1: 60*24*30,
                Interval.YEAR_1: 60*24*365,
            }
            computed_minutes_count = map_minute_count[self.interval]
            qs = Kline.objects.filter(
                symbol=self.symbol,
                open_time__lte=index + timedelta(minutes=computed_minutes_count),
                open_time__gte=index - timedelta(minutes=self.kline_count * computed_minutes_count),
            )
            qs = qs.group_by_interval(self.interval)
            source_df = qs.to_dataframe(index='open_time_group')

        # Преобразовываем значение index в интервал source_df
        if self.interval == Interval.HOUR_1:
            index = index.replace(minute=0)
        elif self.interval == Interval.DAY_1:
            index = index.replace(minute=0, hour=0)
        elif self.interval == Interval.WEEK_1:
            index = index.replace(minute=0, hour=0)
        elif self.interval == Interval.MONTH_1:
            index = index.replace(minute=0, hour=0, day=0)
        elif self.interval == Interval.YEAR_1:
            index = index.replace(minute=0, hour=0, day=0, month=0)

        try:
            _ = source_df.loc[index]
        except KeyError:
            return

        prepared_source_df = source_df.loc[:index].tail(self.kline_count)
        if len(prepared_source_df) < self.kline_count:
            return

        if self.type == self.Type.SMA:
            return self._get_sma_value(prepared_source_df)
        elif self.type == self.Type.EMA:
            return

    def _get_sma_value(self, df: DataFrame) -> Optional[Decimal]:
        average_price_sum = Decimal(0)
        for idx, row in df.iterrows():
            if self.data_source == self.DataSource.OPEN:
                average_price_sum += row['open_price']
            elif self.data_source == self.DataSource.CLOSE:
                average_price_sum += row['close_price']
            elif self.data_source == self.DataSource.HIGH:
                average_price_sum += row['high_price']
            elif self.data_source == self.DataSource.LOW:
                average_price_sum += row['low_price']
            elif self.data_source == self.DataSource.HIGH_LOW:
                average_price_sum += (row['high_price'] + row['low_price']) / 2
            elif self.data_source == self.DataSource.OPEN_CLOSE:
                average_price_sum += (row['open_price'] + row['close_price']) / 2
            else:
                return

        return average_price_sum / self.kline_count
