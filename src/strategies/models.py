from django.db import models
from core.utils.db_utils import BaseModel
from market_data.models import ExchangeInfo, Kline
from market_data.constants import Interval, AllowedInterval
import pandas as pd


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

    class Meta:
        verbose_name = 'Strategy'
        verbose_name_plural = 'Strategies'

    def __str__(self):
        return self.name

    def run(self):
        """
        Запуск стратегии, заполнение StrategyResult
        """
        StrategyResult.objects.filter(strategy_id=self.id).delete()

        kline_qs = Kline.objects.filter(
            symbol=self.base_symbol,
            open_time__gte=self.start_time,
            open_time__lte=self.end_time,
        )
        kline_df = kline_qs.group_by_interval().to_dataframe(index='open_time_group')

        moving_average = self.movingaverage_set.get(codename='MA_1')
        source_df = moving_average.get_source_df(kline_df)

        for idx, kline_item in kline_df.iterrows():

            # находим позицию индекса текущей свечи, если 0 то пропускаем итерацию
            if not (index_position := kline_df.index.get_loc(idx)):
                continue

            previous_index = kline_df.index[index_position - 1]

            previous_ma_value = moving_average.get_value_by_index(
                index=previous_index,
                source_df=source_df,
            )

            # проверяем, что цена пересекла значение MA за предыдущую свечу
            if kline_item['high_price'] > previous_ma_value > kline_item['low_price']:

                # Проверяем, пересечение снизу или сверху, открываем позицию sell or buy
                previous_close_price = kline_df.loc[previous_index, 'close_price']
                if previous_close_price < previous_ma_value:
                    # идем вверх, покупаем
                    StrategyResult.objects.create(
                        strategy_id=self.id,
                        kline=kline_qs.get(open_time=idx),
                        buy=previous_ma_value,
                    )
                else:
                    # идем вниз, продаем
                    StrategyResult.objects.create(
                        strategy_id=self.id,
                        kline=kline_qs.get(open_time=idx),
                        sell=previous_ma_value,
                    )


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
