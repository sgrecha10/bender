from django.db import models

from core.utils.db_utils import BaseModel
# from indicators.models import MovingAverage, StandardDeviation
from market_data.models import Kline, ExchangeInfo
from market_data.constants import AllowedInterval, MAP_MINUTE_COUNT
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional, Type
import statsmodels.api as sm
import numpy as np
from decimal import Decimal
import logging
import pandas as pd
import psycopg2
from django.db import connection

logger = logging.getLogger(__name__)


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

    class SymbolsRatioType(models.TextChoices):
        ONE_TO_ONE = 'one_to_one', 'One to one'
        PRICE = 'price', 'By price ratio on opening deal'
        B_FACTOR = 'b_factor', 'By b-factor'

    class CorrectionType(models.TextChoices):
        NONE = 'none', 'None'
        EVERY_TIME = 'every_time', 'Every time'

    class DataSource(models.TextChoices):
        CROSS_COURSE = 'cross_course', 'Cross course'
        BETA_SPREAD = 'beta_spread', 'Beta spread'
        BETA_SPREAD_LOG = 'beta_spread_log', 'Beta spread log'

    class CorrType(models.TextChoices):
        PEARSON = 'pearson', 'Pearson'

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
        help_text='Задает базовую цену для расчета beta, cross course, corr (analytics).'
    )
    data_source = models.CharField(
        max_length=20,
        choices=DataSource.choices,
        default=DataSource.CROSS_COURSE,
        verbose_name='Data source',
        help_text='Выбор данных для работы стратегии',
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
        choices=SymbolsRatioType.choices,
        default=SymbolsRatioType.PRICE,
        verbose_name='Ratio type',
        help_text='Определение соотношения инструментов на входе в сделку',
    )
    correction_type = models.CharField(
        choices=CorrectionType.choices,
        default=CorrectionType.NONE,
        verbose_name='Correction type',
    )
    entry_price_order = models.CharField(
        max_length=50,
        choices=EntryPriceOrder.choices,
        default=EntryPriceOrder.MAXMIN,
        verbose_name='Entry price order',
        help_text='В каком порядке подавать цены свечи при тестировании стратегии',
    )
    entry_price_interval = models.CharField(
        choices=[
            ('1min', 'Minute 1'),
            ('1D', 'Day 1'),
        ],
        default=AllowedInterval.MINUTE_1,
        max_length=10,
        verbose_name='Entry price interval',
        help_text='Интервал входных свечей при тестировании стратегии',
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

    corr_window = models.PositiveSmallIntegerField(
        default=30,
        verbose_name='Corr window',
        help_text='Окно для расчета корреляции.'
    )
    corr_type = models.CharField(
        choices=CorrType.choices,
        default=CorrType.PEARSON,
        verbose_name='Corr type',
    )
    corr_open_deal_value = models.FloatField(
        default=0.85,
        verbose_name='Corr open deal value',
        help_text='Значение корреляции для открытия сделки, не менее. Если 0 - не используется.',
    )
    corr_stop_loss_value = models.FloatField(
        default=0.85,
        verbose_name='Corr stop loss value',
        help_text='Значение корреляции для срабатывания stop loss, менее. Если 0 - не используется.',
    )

    class Meta:
        verbose_name = 'Arbitration'
        verbose_name_plural = 'Arbitrations'

    def __str__(self):
        return f'{self.codename} - {self.symbol_1} : {self.symbol_2}'

    def get_qs_start_time(self, start_time: datetime) -> datetime:
        """ Возвращает start_time с учетом необходимого запаса для корректного расчета индикаторов. """

        moving_average = self.movingaverage_set.first()
        standard_deviation = self.standarddeviation_set.first()
        beta_factor = self.betafactor_set.first()

        moving_average_converted_to_minutes = (
                moving_average.window_size * MAP_MINUTE_COUNT[self.interval]
        )
        standard_deviation_converted_to_minutes = (
            standard_deviation.window_size * MAP_MINUTE_COUNT[self.interval]
        )
        # прибавляем moving_average_converted_to_minutes, т.к если ma применяется к beta то у беты должен быть еще более ранний запас
        beta_factor_converted_to_minutes = (
            beta_factor.window_size * MAP_MINUTE_COUNT[self.interval]
            + moving_average_converted_to_minutes
            + standard_deviation_converted_to_minutes
        )

        max_minutes = max(
            moving_average_converted_to_minutes,
            standard_deviation_converted_to_minutes,
            beta_factor_converted_to_minutes,
        )
        return start_time - timedelta(minutes=max_minutes)

    def get_symbol_df(self,
                      symbol_pk: str | Type[int],
                      qs_start_time: Optional[datetime] = None,
                      qs_end_time: Optional[datetime] = None) -> pd.DataFrame:
        """ Возвращает df указанного символа за указанный период. """
        data = {'symbol_id': symbol_pk}
        if qs_start_time:
            data.update({'open_time__gte': qs_start_time})
        if qs_end_time:
            data.update({'open_time__lte': qs_end_time})
        kline_list = list(
            Kline.objects.filter(**data).values(
                'open_time',
                'open_price',
                'high_price',
                'low_price',
                'close_price',
                'volume',
            )
        )
        df = pd.DataFrame(kline_list)
        df.set_index("open_time", inplace=True)
        return df

    def _get_symbols_df(self, start_time: datetime = None, end_time: datetime = None) -> pd.DataFrame:
        """ Возвращает df по двум инструментам в одной строке """
        logger.info('Started')

        query = """
        SELECT 
            t1.open_time,
            t1.open_price  AS df_1_open_price,
            t1.high_price  AS df_1_high_price,
            t1.low_price   AS df_1_low_price,
            t1.close_price AS df_1_close_price,
            t2.open_price  AS df_2_open_price,
            t2.high_price  AS df_2_high_price,
            t2.low_price   AS df_2_low_price,
            t2.close_price AS df_2_close_price
        FROM 
            (SELECT * FROM market_data_kline WHERE symbol_id = %s) t1
        FULL JOIN 
            (SELECT * FROM market_data_kline WHERE symbol_id = %s) t2
        ON t1.open_time = t2.open_time
        WHERE t1.open_time BETWEEN %s AND %s
        ORDER BY t1.open_time;
        """

        with connection.cursor() as cursor:
            cursor.execute(
                query,
                [
                    self.symbol_1.symbol,
                    self.symbol_2.symbol,
                    start_time or self.start_time,
                    end_time or self.end_time,
                ],
            )
            logger.info('Got source_qs')

            df = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
            logger.info('Got source_df cursor.fetchall()')

        df.set_index("open_time", inplace=True)
        logger.info('Set index')

        resample_df = df.resample(self.interval).agg({
            'df_1_open_price': 'first',
            'df_1_high_price': 'max',
            'df_1_low_price': 'min',
            'df_1_close_price': 'last',
            'df_2_open_price': 'first',
            'df_2_high_price': 'max',
            'df_2_low_price': 'min',
            'df_2_close_price': 'last',
        })
        logger.info('Resampled df')
        logger.info('Source_df ready')
        return resample_df

    def _get_cross_course_df(self, df: pd.DataFrame) -> pd.Series:
        return (df[f'df_1_{self.price_comparison}'] / df[f'df_2_{self.price_comparison}']).astype(np.float64)

    def _get_beta_factor_df(self, df: pd.DataFrame) -> pd.Series:
        beta_factor = self.betafactor_set.first()
        return beta_factor.get_data(
            source_df=df,
            price_comparison=self.price_comparison,
        ).reindex(df.index, method='ffill')

    def _get_moving_average(self, df: pd.DataFrame) -> pd.Series:
        moving_average = self.movingaverage_set.first()
        return moving_average.get_data(
                source_df=df,
                data_source=self.data_source,
        ).reindex(df.index, method='ffill')

    def _get_standard_deviation(self, df: pd.DataFrame) -> pd.Series:
        standard_deviation = self.standarddeviation_set.first()
        return standard_deviation.get_data(
            source_df=df,
            data_source=self.data_source,
        ).reindex(df.index, method='ffill')

    def _get_corr(self, df: pd.DataFrame) -> pd.Series:
        if self.corr_type == self.CorrType.PEARSON:
            return df[f'df_1_{self.price_comparison}'].rolling(
                window=self.corr_window,
            ).corr(df[f'df_2_{self.price_comparison}'])

    def _get_beta_spread_df(self, df: pd.DataFrame) -> pd.Series:
        beta_factor = self.betafactor_set.first()
        if beta_factor.market_symbol == beta_factor.MarketSymbol.SYMBOL_2:
            return (
                    df[f'df_1_{self.price_comparison}'].astype(np.float64)
                    - df[f'df_2_{self.price_comparison}'].astype(np.float64) * df['beta']
            )
        else:
            return (
                    df[f'df_2_{self.price_comparison}'].astype(np.float64)
                    - df[f'df_1_{self.price_comparison}'].astype(np.float64) * df['beta']
            )

    def get_source_df(self,
                      start_time: datetime = None,
                      end_time: datetime = None) -> pd.DataFrame:

        prepared_start_time = self.get_qs_start_time(start_time=start_time)
        df = self._get_symbols_df(prepared_start_time, end_time)
        df['cross_course'] = self._get_cross_course_df(df)
        df['beta'] = self._get_beta_factor_df(df)
        df['beta_spread'] = self._get_beta_spread_df(df)
        df['moving_average'] = self._get_moving_average(df)
        df['absolute_spread'] = df[self.data_source] - df['moving_average']
        df['standard_deviation'] = self._get_standard_deviation(df)
        df['relative_spread'] = df['absolute_spread'] / df['standard_deviation']
        df['corr'] = self._get_corr(df)

        return df.loc[start_time:end_time]


class ArbitrationDeal(BaseModel):
    """Arbitration History Data"""

    class State(models.TextChoices):
        OPEN = 'open', 'Open'
        CLOSE = 'close', 'Close'
        CORRECTION = 'correction', 'Correction'
        STOP_LOSS_CORR = 'stop_loss_corr', 'Stop-loss by correlation'

    arbitration = models.ForeignKey(
        Arbitration,
        on_delete=models.CASCADE,
        verbose_name='Arbitration',
    )
    symbol = models.ForeignKey(
        ExchangeInfo,
        on_delete=models.CASCADE,
        verbose_name='Symbol',
    )
    deal_time = models.DateTimeField(
        verbose_name='Deal time',
    )
    deal_uid = models.UUIDField(
        verbose_name='Deal UID',
        null=True,
    )
    price = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True, blank=True,
        verbose_name='Price',
        help_text='+ short position, - long position',
    )
    quantity = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        default=0,
        verbose_name='Quantity',
    )
    state = models.CharField(
        choices=State.choices,
        verbose_name='State',
    )
    buy = models.DecimalField(
        verbose_name='Buy',
        max_digits=20,
        decimal_places=10,
        null=True, blank=True,
    )
    sell = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True, blank=True,
        verbose_name='Sell',
    )
    beta_quantity_1 = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True, blank=True,
        verbose_name='Beta quantity 1',
    )
    beta_quantity_2 = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True, blank=True,
        verbose_name='Beta quantity 2',
    )

    class Meta:
        verbose_name = 'Arbitration Deal'
        verbose_name_plural = 'Arbitration Deals'
        indexes = [
            models.Index(fields=['arbitration', 'symbol', 'deal_time']),
            models.Index(fields=['arbitration', 'symbol', 'state', 'deal_time']),
        ]

    def __str__(self):
        return self.arbitration.codename
