from django.db import models

from core.utils.db_utils import BaseModel
from indicators.models import MovingAverage, StandardDeviation
from market_data.models import Kline, ExchangeInfo
from market_data.constants import AllowedInterval


class Arbitration(BaseModel):

    class EntryPriceOrder(models.TextChoices):
        OPEN = 'OPEN', 'Open price'
        CLOSE = 'CLOSE', 'Close price'
        HIGH = 'HIGH', 'High price'
        LOW = 'LOW', 'Low price'
        MAXMIN = 'MAXMIN', 'MaxMin'
        MINMAX = 'MINMAX', 'MinMax'

    class PriceComparison(models.TextChoices):
        OPEN = 'open_price', 'Open price'
        CLOSE = 'close_price', 'Close price'
        HIGH = 'high_price', 'High price'
        LOW = 'low_price', 'Low price'

    class RatioType(models.TextChoices):
        PRICE = 'price', 'By price ratio on opening deal'

    codename = models.CharField(
        max_length=100,
        verbose_name='Codename',
    )
    symbol_1 = models.ForeignKey(
        ExchangeInfo,
        on_delete=models.SET_NULL,
        null=True,
        related_name='arbitration_set_first',
        verbose_name='Symbol 1',
    )
    symbol_2 = models.ForeignKey(
        ExchangeInfo,
        on_delete=models.SET_NULL,
        null=True,
        related_name='arbitration_set_second',
        verbose_name='Symbol 2',
    )
    interval = models.CharField(
        choices=AllowedInterval.choices,
        default=AllowedInterval.MINUTE_1,
        max_length=10,
        verbose_name='Base interval',
    )
    start_time = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Start time',
    )
    end_time = models.DateTimeField(
        null=True, blank=True,
        verbose_name='End time',
    )
    price_comparison = models.CharField(
        choices=PriceComparison.choices,
        default=PriceComparison.CLOSE,
        verbose_name='Price comparison',
    )
    moving_average = models.ForeignKey(
        MovingAverage,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Moving average',
    )
    standard_deviation = models.ForeignKey(
        StandardDeviation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Standard deviation',
    )
    open_deal_sd = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True, blank=True,
        verbose_name='Open deal SD',
    )
    close_deal_sd = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True, blank=True,
        verbose_name='Close deal SD',
    )
    fixed_bet_amount = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        default=1.0000,
        verbose_name='Fixed bet amount',
        help_text='Сумма двух инструментов в сделке',
    )
    ratio_type = models.CharField(
        max_length=20,
        choices=RatioType.choices,
        default=RatioType.PRICE,
        verbose_name='Ratio type',
        help_text='Определение соотношения инструментов на входе в сделку',
    )
    entry_price_order = models.CharField(
        max_length=50,
        choices=EntryPriceOrder.choices,
        default=EntryPriceOrder.MAXMIN,
        verbose_name='Entry price order',
        help_text='В каком порядке подавать цены свечи при тестировании стратегии',
    )
    maker_commission = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=0,
        verbose_name='Maker commission',
    )
    taker_commission = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=0,
        verbose_name='Taker commission',
    )

    class Meta:
        verbose_name = 'Arbitration'
        verbose_name_plural = 'Arbitrations'

    def __str__(self):
        return f'{self.codename} {self.symbol_1} {self.symbol_2}'
