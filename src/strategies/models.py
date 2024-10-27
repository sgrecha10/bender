from django.db import models
from core.utils.db_utils import BaseModel
from market_data.models import ExchangeInfo, Kline
from market_data.constants import Interval, AllowedInterval


class Strategy(BaseModel):
    name = models.CharField(
        verbose_name='Name',
        max_length=255,
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

    class Meta:
        verbose_name = 'Strategy'
        verbose_name_plural = 'Strategies'

    def __str__(self):
        return self.name

    def run(self):
        """
        Запуск стратегии, заполнение StrategyResult
        """
        pass
        # StrategyResult.objects.filter(strategy_id=self.id).delete()
        #
        # kline_qs = Kline.objects.filter(
        #     symbol=self.base_symbol,
        #     open_time__gte=self.start_time,
        #     open_time__lte=self.end_time,
        # )
        # for kline in kline_qs:
        #     StrategyResult.objects.create(
        #         strategy_id=self.id,
        #         kline=kline,
        #         price=kline.high_price + 5,
        #     )


class StrategyResult(BaseModel):
    strategy = models.ForeignKey(
        Strategy, on_delete=models.CASCADE,
        verbose_name='Strategy',
    )
    kline = models.ForeignKey(
        Kline, on_delete=models.CASCADE,
        verbose_name='Kline',
        blank=True, null=True,
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

    class Meta:
        verbose_name = 'Strategy Result'
        verbose_name_plural = 'Strategy Results'
        indexes = [
            models.Index(fields=['strategy', 'kline']),
        ]

    def __str__(self):
        return self.strategy.name
