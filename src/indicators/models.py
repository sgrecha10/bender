from collections.abc import Hashable
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
    MAP_MINUTE_COUNT = {
        Interval.MINUTE_1: 1,
        Interval.HOUR_1: 60,
        Interval.DAY_1: 60 * 24,
        Interval.WEEK_1: 60 * 24 * 7,
        Interval.MONTH_1: 60 * 24 * 30,
        Interval.YEAR_1: 60 * 24 * 365,
    }

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
        verbose_name = 'Moving Average'
        verbose_name_plural = 'Moving Averages'

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

    def get_source_df(self, base_df: DataFrame = None, **kwargs) -> DataFrame:
        """Возвращает source DataFrame

        Если передан base_df, то ограничивает выборку из бд по максимальному
        и минимальному значению с учетом interval,
        если нет, то выбирает все значения из бд.
        """
        if isinstance(base_df, DataFrame) and not base_df.empty:
            base_df.sort_index(inplace=True)
            min_index = base_df.iloc[0].name
            max_index = base_df.iloc[-1].name

            computed_minutes_count = self.MAP_MINUTE_COUNT[self.interval]
            qs = Kline.objects.filter(
                symbol_id=self.symbol,
                open_time__lte=max_index + timedelta(minutes=computed_minutes_count),
                open_time__gte=min_index - timedelta(minutes=self.kline_count * computed_minutes_count),
                **kwargs
            )
        else:
            qs = Kline.objects.filter(symbol_id=self.symbol, **kwargs)

        qs = qs.group_by_interval(self.interval)
        return qs.to_dataframe(index='open_time_group')

    def get_value_by_index(self,
                           index: datetime | Hashable,
                           source_df: DataFrame = None) -> Optional[Decimal]:
        """Возвращает значение MA рассчитанное на переданный index (open_time) включительно

        :param index: datetime
        :param source_df: DataFrame

        1. Если index не найден в source_df - return None
        2. Если количество свечей для расчета в source_df меньше self.kline_count - return None
        """
        if not isinstance(source_df, DataFrame) or source_df.empty:
            # Генерируем source_df если отсутствует в аргументах
            computed_minutes_count = self.MAP_MINUTE_COUNT[self.interval]
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


class StandardDeviation(BaseModel):

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
    moving_average = models.ForeignKey(
        MovingAverage,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Moving Average',
    )
    data_source = models.CharField(
        verbose_name='Data source',
        max_length=20,
        choices=DataSource.choices,
    )
    kline_count = models.IntegerField(
        verbose_name='K-Line Count',
        help_text='Количество свечей для расчета',
    )

    class Meta:
        verbose_name = 'Standard Deviation'
        verbose_name_plural = 'Standard Deviations'

    def __str__(self):
        return f'{self.id} - {self.codename}'

    def get_value_by_index(self,
                           index: datetime | Hashable,
                           source_df: DataFrame = None) -> Optional[Decimal]:
        """Возвращает значение SD рассчитанное на переданный index (open_time) включительно

        :param index: datetime
        :param source_df: DataFrame

        1. Если index не найден в source_df - return None
        2. Если количество свечей для расчета в source_df меньше self.kline_count - return None
        3. Получаем значение MA
        """
        average_price = self.moving_average.get_value_by_index(index, source_df)

        prepared_source_df = source_df.loc[:index].tail(self.kline_count)
        if len(prepared_source_df) < self.kline_count:
            return

        deviation = Decimal(0)
        for idx, row in prepared_source_df.iterrows():
            if self.data_source == self.DataSource.OPEN:
                deviation += (row['open_price'] - average_price) ** 2
            elif self.data_source == self.DataSource.CLOSE:
                deviation += (row['close_price'] - average_price) ** 2
            elif self.data_source == self.DataSource.HIGH:
                deviation += (row['high_price'] - average_price) ** 2
            elif self.data_source == self.DataSource.LOW:
                deviation += (row['low_price'] - average_price) ** 2
            elif self.data_source == self.DataSource.HIGH_LOW:
                deviation += (((row['high_price'] + row['low_price']) / 2) - average_price) ** 2
            elif self.data_source == self.DataSource.OPEN_CLOSE:
                deviation += (((row['open_price'] + row['close_price']) / 2) - average_price) ** 2
            else:
                return

        return (deviation / self.kline_count) ** Decimal(0.5)


class BollingerBands(BaseModel):
    codename = models.CharField(
        verbose_name='Codename',
        max_length=255,
        unique=True,
    )
    description = models.TextField(
        verbose_name='Description',
        blank=True, default='',
    )
    moving_average = models.ForeignKey(
        MovingAverage,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Moving Average',
    )
    standard_deviation = models.ForeignKey(
        StandardDeviation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Standard Deviation',
    )
    sigma_factor = models.DecimalField(
        verbose_name='Sigma Factor',
        max_digits=5,
        decimal_places=4,
        default=2,
    )

    class Meta:
        verbose_name = 'Bollinger Bands'
        verbose_name_plural = 'Bollinger Bands'

    def __str__(self):
        return f'{self.id} - {self.codename}'

    def get_values_by_index(self,
                           index: datetime | Hashable,
                           source_df: DataFrame = None) -> Optional[tuple]:
        """
        Возвращает кортеж из трех значений.
        """

        average_price = self.moving_average.get_value_by_index(
            index=index,
            source_df=source_df,
        )
        standard_deviation = self.standard_deviation.get_value_by_index(
            index=index,
            source_df=source_df,
        )

        return (
            average_price - standard_deviation * self.sigma_factor,
            average_price,
            average_price + standard_deviation * self.sigma_factor,
        )
