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
# from indicators.models import BetaFactor
from decimal import Decimal
import logging
import pandas as pd
import psycopg2
from django.db import connection

logger = logging.getLogger(__name__)


class Arbitration(BaseModel):
    # ma_cross_course_codename = 'AR_MA_1'
    # ma_beta_spread_codename = 'AR_MA_2'
    #
    # sd_cross_course_codename = 'AR_SD_1'
    # sd_beta_spread_codename = 'AR_SD_2'

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
    correlation_window = models.PositiveSmallIntegerField(
        default=30,
        verbose_name='Correlation window',
        help_text='Аналитический параметр. Окно для расчета корреляции.'
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
            beta_factor.window_size * MAP_MINUTE_COUNT[self.interval] + moving_average_converted_to_minutes + standard_deviation_converted_to_minutes
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
            logger.info('Got source_df')

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

        return resample_df

    def _get_cross_course_df(self, df: pd.DataFrame) -> pd.Series:
        return (df[f'df_1_{self.price_comparison}'] / df[f'df_2_{self.price_comparison}']).astype(float)

    def _get_beta_factor_df(self, df: pd.DataFrame) -> pd.Series:
        beta_factor = self.betafactor_set.first()
        return beta_factor.get_data(
            source_df=df,
            interval=self.interval,
        ).reindex(df.index, method='ffill')

    def _get_moving_average(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        moving_average = self.movingaverage_set.first()
        moving_average_series = moving_average.get_data(
                source_df=df,
                interval=self.interval,
        ).reindex(df.index, method='ffill')
        absolute_spread_series = df[moving_average.data_source] - moving_average_series
        return moving_average_series, absolute_spread_series

    def _get_standard_deviation(self, df: pd.DataFrame) -> pd.Series:
        standard_deviation = self.standarddeviation_set.first()
        return standard_deviation.get_data(
            source_df=df,
            interval=self.interval,
        ).reindex(df.index, method='ffill')

    def _get_corr_pearson(self, df: pd.DataFrame) -> pd.Series:
        return df[f'df_1_{self.price_comparison}'].rolling(
            window=self.correlation_window,
        ).corr(df[f'df_2_{self.price_comparison}'])

    def get_source_df(self,
                      start_time: datetime = None,
                      end_time: datetime = None,
                      is_show_analytics: bool = False) -> pd.DataFrame:

        prepared_start_time = self.get_qs_start_time(start_time=start_time)
        df = self._get_symbols_df(prepared_start_time, end_time)
        df['cross_course'] = self._get_cross_course_df(df)
        df['beta'] = self._get_beta_factor_df(df)
        df['moving_average'], df['absolute_spread'] = self._get_moving_average(df)
        df['standard_deviation'] = self._get_standard_deviation(df)
        df['relative_spread'] = df['absolute_spread'] / df['standard_deviation']

        if is_show_analytics:
            df['corr_pearson'] = self._get_corr_pearson(df)

        return df.loc[start_time:end_time]



        # logger.info('Started')
        # # prepared_start_time = self.get_qs_start_time(start_time=self.start_time)
        #
        # conn = psycopg2.connect("dbname=bender user=bender password=bender host=postgres")
        # query = """
        # SELECT
        #     t1.open_time,
        #     t1.open_price  AS s_1_open_price,
        #     t1.high_price  AS s_1_high_price,
        #     t1.low_price   AS s_1_low_price,
        #     t1.close_price AS s_1_close_price,
        #     t2.open_price  AS s_2_open_price,
        #     t2.high_price  AS s_2_high_price,
        #     t2.low_price   AS s_2_low_price,
        #     t2.close_price AS s_2_close_price
        # FROM
        #     (SELECT * FROM market_data_kline WHERE symbol_id = 'BTCUSDT' AND open_time >= '') t1
        # FULL JOIN
        #     (SELECT * FROM market_data_kline WHERE symbol_id = 'ETHUSDT') t2
        # ON t1.open_time = t2.open_time
        # ORDER BY t1.open_time;
        # """
        #
        # df = pd.read_sql(query, conn)
        # logger.info('Got df')
        #
        # conn.close()
        #
        # return df




    # def get_source_dfs(self) -> tuple:
    #     """ Возвращает 3 датафрейма со сдвигом start_time для всех индикаторов """
    #
    #     logger.info('Started')
    #     prepared_start_time = self.get_qs_start_time(start_time=self.start_time)
    #
    #     df_1 = self.get_symbol_df(
    #         symbol_pk=self.symbol_1_id,
    #         qs_start_time=prepared_start_time,
    #         qs_end_time=self.end_time,
    #     )
    #     logger.info('Got df_1')
    #
    #     resample_df_1 = df_1.resample(self.interval).agg({
    #         'open_price': 'first',
    #         'high_price': 'max',
    #         'low_price': 'min',
    #         'close_price': 'last',
    #         'volume': 'sum',
    #     })
    #     logger.info('Resampled df_1')
    #
    #     df_2 = self.get_symbol_df(
    #         symbol_pk=self.symbol_2_id,
    #         qs_start_time=prepared_start_time,
    #         qs_end_time=self.end_time,
    #     )
    #     logger.info('Got df_2')
    #
    #     resample_df_2 = df_2.resample(self.interval).agg({
    #         'open_price': 'first',
    #         'high_price': 'max',
    #         'low_price': 'min',
    #         'close_price': 'last',
    #         'volume': 'sum',
    #     })
    #     logger.info('Resampled df_2')
    #
    #     source_df = pd.DataFrame(columns=[
    #         'df_1',
    #         'df_2',
    #         'cross_course',
    #     ], dtype=float)
    #
    #     source_df['df_1'] = resample_df_1[self.price_comparison]
    #     source_df['df_2'] = resample_df_2[self.price_comparison]
    #     # source_df.to_csv('out.csv')
    #     source_df['cross_course'] = source_df['df_1'] / source_df['df_2']
    #     logger.info('Got source_df')
    #
    #     return resample_df_1, resample_df_2, source_df



    # И тут ниже надо выпилить
    # def get_source_dfs(self) -> tuple:
    #     """ Возвращает 3 датафрейма со сдвигом start_time для всех индикаторов """
    #
    #     prepared_start_time = self.get_qs_start_time(start_time=self.start_time)
    #
    #     df_1 = self.get_symbol_df(
    #         symbol_pk=self.symbol_1_id,
    #         qs_start_time=prepared_start_time,
    #         qs_end_time=self.end_time,
    #     )
    #     df_2 = self.get_symbol_df(
    #         symbol_pk=self.symbol_2_id,
    #         qs_start_time=prepared_start_time,
    #         qs_end_time=self.end_time,
    #     )
    #     source_df = pd.DataFrame(columns=[
    #         'df_1',
    #         'df_2',
    #         'cross_course',
    #     ], dtype=float)
    #
    #     source_df['df_1'] = df_1[self.price_comparison]
    #     source_df['df_2'] = df_2[self.price_comparison]
    #     # source_df.to_csv('out.csv')
    #     source_df['cross_course'] = source_df['df_1'] / source_df['df_2']
    #
    #     source_df = source_df.resample(self.interval).agg({
    #         'df_1': 'last',
    #         'df_2': 'last',
    #         'cross_course': 'last',
    #     })
    #
    #     #  Cross course
    #     moving_average_cross_course = self.movingaverage_set.get(codename=self.ma_cross_course_codename)
    #     source_df[moving_average_cross_course.codename] = moving_average_cross_course.get_data(
    #         source_df=source_df,
    #         interval=self.interval,
    #     ).reindex(source_df.index, method='ffill')
    #
    #     standard_deviation_cross_course = self.standarddeviation_set.get(codename=self.sd_cross_course_codename)
    #     source_df[standard_deviation_cross_course.codename] = standard_deviation_cross_course.get_data(
    #         source_df=source_df,
    #         interval=self.interval,
    #     ).reindex(source_df.index, method='ffill')
    #
    #     source_df['ad_cross_course'] = (
    #             source_df['cross_course'] - source_df[moving_average_cross_course.codename].apply(Decimal)
    #     )
    #     source_df['sd_cross_course'] = (
    #             source_df['ad_cross_course'] / source_df[standard_deviation_cross_course.codename].apply(Decimal)
    #     )
    #
    #     # Beta spread
    #     beta_factor = self.betafactor_set.first()
    #     source_df['beta'] = beta_factor.get_data(
    #         source_df=source_df,
    #         interval=self.interval,
    #     ).reindex(source_df.index, method='ffill')
    #
    #     source_df['beta_spread'] = (
    #             source_df['df_1'] - source_df['df_2'] * source_df['beta'].apply(Decimal)
    #             if beta_factor.market_symbol == 'symbol_2' else
    #             source_df['df_2'] - source_df['df_1'] * source_df['beta'].apply(Decimal)
    #     )
    #
    #     moving_average_beta_spread = self.movingaverage_set.get(codename=self.ma_beta_spread_codename)
    #     source_df[moving_average_beta_spread.codename] = moving_average_beta_spread.get_data(
    #         source_df=source_df,
    #         interval=self.interval,
    #     ).reindex(source_df.index, method='ffill')
    #
    #     standard_deviation_beta_spread = self.standarddeviation_set.get(codename=self.sd_beta_spread_codename)
    #     source_df[standard_deviation_beta_spread.codename] = standard_deviation_beta_spread.get_data(
    #         source_df=source_df,
    #         interval=self.interval,
    #     ).reindex(source_df.index, method='ffill')
    #
    #     source_df['ad_beta_spread'] = (
    #             source_df['beta_spread'] - source_df[moving_average_beta_spread.codename].apply(Decimal)
    #     )
    #     source_df['sd_beta_spread'] = (
    #             source_df['ad_beta_spread'] / source_df[standard_deviation_beta_spread.codename].apply(Decimal)
    #     )
    #
    #     source_df['pearson'] = source_df['df_1'].rolling(
    #         window=self.correlation_window,
    #     ).corr(source_df['df_2'])
    #     # source_df['spearman'] = source_df['df_1'].rolling(
    #     #     window=self.correlation_window,
    #     # ).corr(
    #     #     source_df['df_2'],
    #     #     method='spearman',
    #     # )
    #
    #     return df_1, df_2, source_df




    #  Ниже надо выпилить методы
    # def _get_df(self,
    #             df_1: pd.DataFrame,
    #             df_2: pd.DataFrame,
    #             start_time: datetime,
    #             end_time: datetime) -> pd.DataFrame:
    #     """Returned DataFrame"""
    #     standard_deviation = self.standarddeviation_set.first()
    #     moving_average = self.movingaverage_set.first()
    #
    #     df_cross_course = pd.DataFrame(columns=['cross_course'], dtype=float)
    #     df_cross_course['cross_course'] = df_1[self.price_comparison] / df_2[self.price_comparison]
    #
    #     df_cross_course = df_cross_course.apply(pd.to_numeric, downcast='float')
    #
    #     if moving_average:
    #         moving_average.calculate_values(df_cross_course, moving_average.codename)
    #         df_cross_course['absolute_deviation'] = (
    #                 df_cross_course['cross_course'] - df_cross_course[moving_average.codename]
    #         )
    #
    #     if standard_deviation:
    #         standard_deviation.calculate_values(df_cross_course, standard_deviation.codename)
    #         df_cross_course['standard_deviation'] = (
    #             df_cross_course['absolute_deviation'] / df_cross_course[standard_deviation.codename]
    #         )
    #
    #     df_cross_course = df_cross_course.loc[start_time:end_time]
    #
    #     # все что ниже вывести в чарт, это исходники для расчета беты
    #     df_cross_course['variance_2'] = df_2[self.price_comparison].rolling(window=self.b_factor_window).var()
    #
    #     df_covariance = pd.DataFrame(columns=['col_1', 'col_2'], dtype=float)
    #     df_covariance['col_1'] = df_1[self.b_factor_price_comparison]
    #     df_covariance['col_2'] = df_2[self.b_factor_price_comparison]
    #
    #     df_covariance_matrix = df_covariance.rolling(
    #         window=self.b_factor_window,
    #     ).cov().dropna().unstack()['col_1']['col_2']
    #
    #     df_cross_course['covariance'] = df_covariance_matrix
    #
    #     df_cross_course['beta'] = df_cross_course['covariance'] / df_cross_course['variance_2']
    #
    #     # df_cross_course['beta_sm'] = self.rolling_beta(
    #     #     df_covariance['col_1'],
    #     #     df_covariance['col_2'],
    #     #     self.b_factor_window,
    #     # )
    #
    #     return df_cross_course
    #
    # # --- Функция для расчёта OLS ---
    # def rolling_beta(self, y, x, window):
    #     """
    #     Рассчитывает коэффициент бета для скользящего окна.
    #     """
    #     n = len(y)  # Длина исходного ряда
    #     betas = []  # Список для сохранения бета-коэффициентов
    #
    #     for start in range(n - window + 1):
    #         # Извлекаем окно данных
    #         y_window = y[start:start + window]
    #         x_window = x[start:start + window]
    #
    #         # Удаляем NaN перед созданием модели
    #         valid_data = pd.concat([y_window, x_window], axis=1).dropna()
    #
    #         # Если в окне нет данных, пропускаем
    #         if len(valid_data) == 0:
    #             betas.append(np.nan)
    #             continue
    #
    #         # Извлекаем очищенные данные
    #         y_clean = valid_data.iloc[:, 0].values.astype(np.float64)  # Зависимая переменная
    #         x_clean = valid_data.iloc[:, 1].values.astype(np.float64)  # Независимая переменная
    #
    #         # Добавляем константу для независимой переменной
    #         X = sm.add_constant(x_clean)
    #
    #         # Строим модель
    #         model = sm.OLS(y_clean, X).fit()
    #
    #         # Сохраняем коэффициент для X
    #         betas.append(model.params[1])
    #
    #     # Добавляем NaN в начало (до первого окна) и в конец (до конца ряда)
    #     return betas[1:]
    #     # result = [np.nan] * (window - 1) + betas
    #     # result = result[:n]  # Обрезаем до длины DataFrame
    #     # return result
    #
    # def get_df(self, start_time: datetime = None, end_time: datetime = None) -> pd.DataFrame:
    #     start_time = start_time or self.start_time
    #     end_time = end_time or self.end_time
    #
    #     qs_start_time = self.get_qs_start_time(start_time=start_time)
    #
    #     df_1 = self.get_symbol_df(
    #         symbol_pk=self.symbol_1_id,
    #         qs_start_time=qs_start_time,
    #         qs_end_time=end_time,
    #     )
    #     df_2 = self.get_symbol_df(
    #         symbol_pk=self.symbol_2_id,
    #         qs_start_time=qs_start_time,
    #         qs_end_time=end_time,
    #     )
    #     return self._get_df(
    #         df_1=df_1,
    #         df_2=df_2,
    #         start_time=start_time,
    #         end_time=end_time,
    #     )


class ArbitrationDeal(BaseModel):
    """Arbitration History Data"""

    class State(models.TextChoices):
        OPEN = 'open', 'Open'
        CLOSE = 'close', 'Close'
        PROFIT = 'profit', 'Profit'
        LOSS = 'loss', 'Loss'
        UNKNOWN = 'unknown', 'Unknown'
        CORRECTION = 'correction', 'Correction'

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
