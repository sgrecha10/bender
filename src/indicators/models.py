from collections.abc import Hashable
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from django.db import models
from pandas import DataFrame

from core.utils.db_utils import BaseModel
from market_data.constants import AllowedInterval, Interval
from market_data.constants import MAP_MINUTE_COUNT
from market_data.models import ExchangeInfo, Kline
from strategies.models import Strategy
from arbitrations.models import Arbitration


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
        CROSS_COURSE = 'cross_course', 'Cross course'

    codename = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Codename',
    )
    description = models.TextField(
        blank=True, default='',
        verbose_name='Description',
    )
    data_source = models.CharField(
        max_length=20,
        choices=DataSource.choices,
        verbose_name='Data source',
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        verbose_name='Type',
    )
    kline_count = models.IntegerField(
        verbose_name='K-Line Count',
        help_text='Количество свечей для расчета',
    )
    factor_alfa = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0,
        verbose_name='Factor Alfa',
        help_text='Используется для расчета EMA',
    )
    factor_alfa_auto = models.BooleanField(
        default=False,
        verbose_name='Factor Alfa Auto',
        help_text='Используется для расчета EMA',
    )
    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Strategy',
    )
    arbitration = models.ForeignKey(
        Arbitration,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Arbitration',
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

            computed_minutes_count = MAP_MINUTE_COUNT[self.interval]
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
            computed_minutes_count = MAP_MINUTE_COUNT[self.interval]
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

    def calculate_values(self, df: DataFrame, column_name: str) -> None:
        """Добавляет в переданный df колонку с значением
        """
        df[column_name] = df[self.data_source].rolling(window=self.kline_count).mean()


class StandardDeviation(BaseModel):

    class DataSource(models.TextChoices):
        OPEN = 'open', 'Open price'
        CLOSE = 'close', 'Close price'
        HIGH = 'high', 'High price'
        LOW = 'low', 'Low price'
        HIGH_LOW = 'high_low', 'High-Low average'
        OPEN_CLOSE = 'open_close', 'Open-Close average'
        CROSS_COURSE = 'cross_course', 'Cross course'

    codename = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Codename',
    )
    description = models.TextField(
        blank=True, default='',
        verbose_name='Description',
    )
    moving_average = models.ForeignKey(
        MovingAverage,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Moving Average',
    )
    data_source = models.CharField(
        max_length=20,
        choices=DataSource.choices,
        verbose_name='Data source',
    )
    kline_count = models.IntegerField(
        verbose_name='K-Line Count',
        help_text='Количество свечей для расчета',
    )
    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Strategy',
    )
    arbitration = models.ForeignKey(
        Arbitration,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Arbitration',
    )

    class Meta:
        verbose_name = 'Standard Deviation'
        verbose_name_plural = 'Standard Deviations'

    def __str__(self):
        return (
            f'{self.id} - '
            f'{self.codename} - '
            f'{self.moving_average and self.moving_average.codename} - '
            f'{self.get_data_source_display()} - '
            f'{self.kline_count}'
        )

    def get_source_df(self, base_df: DataFrame = None, **kwargs) -> DataFrame:
        """Возвращает source DataFrame

        Алгоритм как у moving_average, за исключением того, что kline_count выбирается большее между опорным MA
        и собственной настройкой у SD
        """
        if isinstance(base_df, DataFrame) and not base_df.empty:
            base_df.sort_index(inplace=True)
            min_index = base_df.iloc[0].name
            max_index = base_df.iloc[-1].name

            computed_minutes_count = MAP_MINUTE_COUNT[self.moving_average.interval]
            kline_count = max(self.kline_count, self.moving_average.kline_count)
            qs = Kline.objects.filter(
                symbol_id=self.moving_average.symbol,
                open_time__lte=max_index + timedelta(minutes=computed_minutes_count),
                open_time__gte=min_index - timedelta(minutes=kline_count * computed_minutes_count),
                **kwargs
            )
        else:
            qs = Kline.objects.filter(symbol_id=self.moving_average.symbol, **kwargs)

        qs = qs.group_by_interval(self.moving_average.interval)
        return qs.to_dataframe(index='open_time_group')

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
        if not (average_price := self.moving_average.get_value_by_index(index, source_df)):
            return

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

    def calculate_values(self, df: DataFrame, column_name: str) -> None:
        """Добавляет в переданный df колонку с значением
        """
        df[column_name] = df[self.data_source].rolling(window=self.kline_count).std()


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
