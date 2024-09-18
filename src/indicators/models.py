from datetime import datetime
from decimal import Decimal
from typing import Optional

from django.db import models
from pandas import DataFrame

from core.utils.db_utils import BaseModel
from market_data.constants import AllowedInterval
from market_data.models import ExchangeInfo
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

    name = models.CharField(
        verbose_name='Name',
        max_length=255,
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
        null=True, blank=True,
    )
    interval = models.CharField(
        verbose_name='Interval',
        choices=AllowedInterval.choices,
        max_length=10,
        null=True, blank=True,
    )
    is_use_own_df = models.BooleanField(
        verbose_name='Use own DF',
        default=False,
    )

    class Meta:
        verbose_name = 'MovingAverage'
        verbose_name_plural = 'MovingAverage'

    def __str__(self):
        return (
            f'{self.id} '
            f'- {self.name}'
            f'- {self.get_type_display()} '
            f'- {self.kline_count} '
            f'- {self.get_data_source_display()} '
            f'- {self.is_use_own_df} '
        )

    def get_value_by_index(self,
                           index: datetime,
                           df: DataFrame = None) -> Optional[Decimal]:
        """Возвращает значение MA рассчитанное на переданный open_time включительно

        symbol, interval - если есть, не использовать переданный df

        1. Если index не найден в df - return None
        2. Если количество свечей для расчета в df меньше self.kline_count - return None
        2. Считаем МА:
        2.1. SMA.
            Сумма средних значений (high_price + low_price) / 2  деленное на количество kline_count
        2.2. EMA.
        """

        if self.is_use_own_df:
            pass

        # if self.symbol and self.interval:
        #     pass
        #     df = ...

        try:
            _ = df.loc[index]
        except KeyError:
            return

        df_prepared = df.loc[:index].tail(self.kline_count)
        if len(df_prepared) < self.kline_count:
            return

        if self.type == self.Type.SMA:
            return self._get_sma_value(df_prepared)
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
