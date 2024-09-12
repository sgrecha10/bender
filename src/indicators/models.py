from decimal import Decimal
from typing import Optional

from django.db import models

from core.utils.db_utils import BaseModel
from market_data.constants import AllowedInterval
from market_data.models import ExchangeInfo, Kline
from pandas import DataFrame
from datetime import datetime


class MovingAverage(BaseModel):
    class Type(models.TextChoices):
        SMA = 'sma', 'SMA'
        EMA = 'ema', 'EMA'

    name = models.CharField(
        verbose_name='Name',
        max_length=255,
    )
    description = models.TextField(
        verbose_name='Description',
        blank=True, default='',
    )
    type = models.CharField(
        verbose_name='Type',
        max_length=255,
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
    symbol = models.ForeignKey(
        ExchangeInfo,
        on_delete=models.CASCADE,
        verbose_name='Symbol',
    )
    interval = models.CharField(
        verbose_name='Interval',
        choices=AllowedInterval.choices,
    )

    class Meta:
        verbose_name = 'MovingAverage'
        verbose_name_plural = 'MovingAverage'

    def __str__(self):
        return f'{self.id} - {self.type} - {self.name}'

    def get_value_by_index(self,
                           df: DataFrame,
                           open_time: datetime) -> Optional[Decimal]:
        """Возвращает значение MA рассчитанное на переданный open_time включительно

        symbol, interval - не используются

        1. Если open_time не найден в df - return None
        2. Считаем МА:
        2.1. SMA.
            Сумма средних значений (high_price + low_price) / 2  деленное на количество kline_count
        2.2. EMA.
        """

        try:
            _ = df.loc[open_time]
        except KeyError:
            return

        df_prepared = df.loc[:open_time].tail(self.kline_count)
        average_price_sum = Decimal(0)
        for idx, row in df_prepared.iterrows():
            high_price = row['high_price']
            low_price = row['low_price']
            average_price_sum += (high_price + low_price) / 2

        return average_price_sum / self.kline_count
