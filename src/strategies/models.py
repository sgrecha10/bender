from PIL.ImageCms import Direction
from django.db import models
from core.utils.db_utils import BaseModel
from market_data.models import ExchangeInfo, Kline
from market_data.constants import Interval, AllowedInterval
import pandas as pd


class Strategy(BaseModel):
    class Codename(models.TextChoices):
        STRATEGY_1 = 'strategy_1', 'Strategy_1'
        STRATEGY_ANNA = 'strategy_anna', 'Anna'

    class Direction(models.TextChoices):
        DEFAULT = 'default', 'Default'
        ONLY_SELL = 'only_sell', 'Only sell'
        ONLY_BUY = 'only_buy', 'Only buy'

    class EntryPriceOrder(models.TextChoices):
        OPEN = 'OPEN', 'Open price'
        CLOSE = 'CLOSE', 'Close price'
        HIGH = 'HIGH', 'High price'
        LOW = 'LOW', 'Low price'
        MAXMIN = 'MAXMIN', 'MaxMin'
        MINMAX = 'MINMAX', 'MinMax'

    codename = models.CharField(
        verbose_name='Codename',
        max_length=255,
        choices=Codename.choices,
        unique=True,
    )
    description = models.TextField(
        verbose_name='Description',
        blank=True, default='',
    )

    base_symbol = models.ForeignKey(
        ExchangeInfo,
        on_delete=models.CASCADE,
        related_name='strategies_base_symbol',
        verbose_name='Base symbol',
        null=True, blank=True,
    )
    base_interval = models.CharField(
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
    stop_loss_factor = models.DecimalField(
        verbose_name='Stop loss factor',
        max_digits=5,
        decimal_places=4,
        default=1,
    )
    take_profit_factor = models.DecimalField(
        verbose_name='Take profit factor',
        max_digits=5,
        decimal_places=4,
        default=2,
    )
    fixed_bet_amount = models.DecimalField(
        verbose_name='Fixed bet amount',
        max_digits=20,
        decimal_places=10,
        default=0.00001,
    )
    direction_deals = models.CharField(
        verbose_name='Direction deals',
        help_text='Если default то тренд определяется самой стратегией',
        max_length=50,
        choices=Direction.choices,
        default=Direction.DEFAULT,
    )
    entry_price_order = models.CharField(
        verbose_name='Entry price order',
        help_text='В каком порядке подавать цены свечи при тестировании стратегии',
        max_length=50,
        choices=EntryPriceOrder.choices,
        default=EntryPriceOrder.MAXMIN,
    )
    maker_commission = models.DecimalField(
        verbose_name='Maker commission',
        max_digits=4,
        decimal_places=3,
        default=0,
    )
    taker_commission = models.DecimalField(
        verbose_name='Taker commission',
        max_digits=4,
        decimal_places=3,
        default=0,
    )

    class Meta:
        verbose_name = 'Strategy'
        verbose_name_plural = 'Strategies'

    def __str__(self):
        return self.get_codename_display()


class StrategyResult(BaseModel):
    class State(models.TextChoices):
        OPEN = 'open', 'Open'
        PROFIT = 'profit', 'Profit'
        LOSS = 'loss', 'Loss'
        UNKNOWN = 'unknown', 'Unknown'

    strategy = models.ForeignKey(
        Strategy, on_delete=models.CASCADE,
        verbose_name='Strategy',
    )
    deal_time = models.DateTimeField(
        verbose_name='Deal time',
    )
    buy = models.DecimalField(
        verbose_name='Buy',
        max_digits=20,
        decimal_places=10,
        null=True, blank=True,
    )
    sell = models.DecimalField(
        verbose_name='Sell',
        max_digits=20,
        decimal_places=10,
        null=True, blank=True,
    )
    state = models.CharField(
        verbose_name='State',
        choices=State.choices,
    )

    class Meta:
        verbose_name = 'Strategy Result'
        verbose_name_plural = 'Strategy Results'
        indexes = [
            models.Index(fields=['strategy', 'deal_time']),
        ]

    def __str__(self):
        return self.strategy.codename
