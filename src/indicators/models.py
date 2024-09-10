from decimal import Decimal
from typing import Optional

from django.db import models

from core.utils.db_utils import BaseModel
from market_data.models import ExchangeInfo, Kline
from market_data.constants import Interval


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
        choices=Interval.choices,
    )

    class Meta:
        verbose_name = 'MovingAverage'
        verbose_name_plural = 'MovingAverage'

    def __str__(self):
        return f'{self.id} - {self.type} - {self.name}'

    def get_value(self, kline: Kline) -> Optional[Decimal]:
        """Возвращает значение рассчитанное на переданную свечу (закрытую или в реалтайме)

        1. Проверить, что размер свечи kline (close_time - open_time) не больше, чем self.interval
        3. Преобразовать kline в свечу interval размера
        4. Получаем запрос из postgres от kline.open_time свечи длиной kline_count * interval.minutes_count
        5. Преобразовываем в DataFrame и считаем MA:
        5.1. SMA.
            Сумма средних значений (high_price + low_price) / 2  деленное на количество kline_count
        5.2. EMA.
        """
        return Decimal(25.0)
