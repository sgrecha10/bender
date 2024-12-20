from django.db import models

from core.utils.db_utils import BaseModel
from market_data.models import Kline, ExchangeInfo
from market_data.constants import AllowedInterval


class Arbitration(BaseModel):

    class PriceComparison(models.TextChoices):
        OPEN = 'OPEN', 'Open price'
        CLOSE = 'CLOSE', 'Close price'
        HIGH = 'HIGH', 'High price'
        LOW = 'LOW', 'Low price'

    codename = models.CharField(
        verbose_name='Codename',
        max_length=100,
    )
    symbol_1 = models.ForeignKey(
        ExchangeInfo,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Symbol 1',
        related_name='arbitration_set_first',
    )
    symbol_2 = models.ForeignKey(
        ExchangeInfo,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Symbol 2',
        related_name='arbitration_set_second',
    )
    interval = models.CharField(
        verbose_name='Base interval',
        choices=AllowedInterval.choices,
        default=AllowedInterval.MINUTE_1,
        max_length=10,
    )
    start_time = models.DateTimeField(
        verbose_name='Start time',
        null=True, blank=True,
    )
    end_time = models.DateTimeField(
        verbose_name='End time',
        null=True, blank=True,
    )
    price_comparison = models.CharField(
        verbose_name='Price comparison',
        choices=PriceComparison.choices,
        default=PriceComparison.CLOSE,
    )

    class Meta:
        verbose_name = 'Arbitration'
        verbose_name_plural = 'Arbitrations'

    def __str__(self):
        return f'{self.codename} {self.symbol_1} {self.symbol_2}'
