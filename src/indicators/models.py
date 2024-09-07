from decimal import Decimal
from typing import Optional

from django.db import models

from core.utils.db_utils import BaseModel
from market_data.models import ExchangeInfo, Interval, Kline


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
    interval = models.ForeignKey(
        Interval,
        on_delete=models.CASCADE,
        verbose_name='Interval',
    )

    class Meta:
        verbose_name = 'MovingAverage'
        verbose_name_plural = 'MovingAverage'

    def __str__(self):
        return f'{self.id} - {self.type} - {self.name}'

    def get_value(self, kline: Kline) -> Optional[Decimal]:
        """Возвращает значение рассчитанное на переданную свечу"""
        pass
