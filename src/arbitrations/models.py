from django.db import models

from core.utils.db_utils import BaseModel
from indicators.models import MovingAverage, StandardDeviation
from market_data.models import Kline, ExchangeInfo
from market_data.constants import AllowedInterval, MAP_MINUTE_COUNT
from datetime import datetime, timedelta
import pandas as pd


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

    def get_qs_start_time(self):
        kline_max = max(self.moving_average.kline_count, self.moving_average.kline_count)
        computed_minutes_count = MAP_MINUTE_COUNT[self.interval]
        prepared_kline_max = kline_max * computed_minutes_count
        return self.start_time - timedelta(minutes=prepared_kline_max)

    def get_symbol_df(self, symbol_pk: str, qs_start_time: datetime):
        qs = Kline.objects.filter(symbol_id=symbol_pk)
        qs = qs.filter(open_time__gte=qs_start_time) if qs_start_time else qs
        qs = qs.group_by_interval(self.interval)
        return qs.to_dataframe(index='open_time_group')

    def get_df(self, df_1: pd.DataFrame, df_2: pd.DataFrame):
        """Returned DataFrame"""
        start_time = self.start_time
        end_time = self.end_time

        moving_average = self.moving_average
        standard_deviation = self.standard_deviation

        # kline_max = max(moving_average.kline_count, moving_average.kline_count)
        # computed_minutes_count = MAP_MINUTE_COUNT[self.interval]
        # prepared_kline_max = kline_max * computed_minutes_count
        # qs_start_time = start_time - timedelta(minutes=prepared_kline_max)

        # df_1 = self.get_symbol_df(
        #     symbol_pk=self.symbol_1_id,
        #     qs_start_time=qs_start_time,
        # )
        # df_2 = self.get_symbol_df(
        #     symbol_pk=self.symbol_2_id,
        #     qs_start_time=qs_start_time,
        # )

        df_cross_course = pd.DataFrame(columns=['cross_course'], dtype=float)
        df_cross_course['cross_course'] = df_1[self.price_comparison] / df_2[self.price_comparison]

        # df_cross_course['cross_course'].apply(float)
        df_cross_course = df_cross_course.apply(pd.to_numeric, downcast='float')

        moving_average.calculate_values(df_cross_course, moving_average.codename)
        standard_deviation.calculate_values(df_cross_course, standard_deviation.codename)

        df_cross_course['absolute_deviation'] = (
                df_cross_course['cross_course'] - df_cross_course[moving_average.codename]
        )

        df_cross_course['standard_deviation'] = (
            (df_cross_course['cross_course'] - df_cross_course[moving_average.codename])
            / df_cross_course[standard_deviation.codename]
        )

        # df_1 = df_1.loc[start_time:end_time]
        # df_2 = df_2.loc[start_time:end_time]
        df_cross_course = df_cross_course.loc[start_time:end_time]

        return df_cross_course
