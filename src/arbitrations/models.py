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


class Arbitration(BaseModel):
    ma_cross_course_codename = 'AR_MA_1'
    ma_beta_spread_codename = 'AR_MA_2'

    sd_cross_course_codename = 'AR_SD_1'
    sd_beta_spread_codename = 'AR_SD_2'

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

    class ZIndex(models.TextChoices):
        CROSS_COURSE = 'cross_course', 'Cross course'
        BETA_SPREAD = 'beta_spread', 'Beta spread'

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
        help_text='Задает базовый интервал. Интервалы в индикаторах могут быть больше, но не меньше.'
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
        help_text='Задает базовую цену для расчета индикаторов и cross course.'
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
    z_index = models.CharField(
        choices=ZIndex.choices,
        default=ZIndex.CROSS_COURSE,
        verbose_name='Z-Index',
        help_text='Выбор способа определения спреда для арбитража',
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

    class Meta:
        verbose_name = 'Arbitration'
        verbose_name_plural = 'Arbitrations'

    def __str__(self):
        return f'{self.codename} - {self.symbol_1} : {self.symbol_2}'

    def get_qs_start_time(self, start_time: datetime) -> datetime:
        """ Возвращает start_time с учетом необходимого запаса для корректного расчета индикаторов. """

        beta_factor = self.betafactor_set.first()

        standard_deviation_cross_course = self.standarddeviation_set.get(codename=self.sd_cross_course_codename)
        standard_deviation_beta_spread = self.standarddeviation_set.get(codename=self.sd_beta_spread_codename)

        moving_average_cross_course = self.movingaverage_set.get(codename=self.ma_cross_course_codename)
        moving_average_beta_spread = self.movingaverage_set.get(codename=self.ma_beta_spread_codename)

        moving_average_converted_to_minutes = (
                moving_average_cross_course.kline_count * MAP_MINUTE_COUNT[moving_average_cross_course.interval]
        )
        standard_deviation_cross_course_converted_to_minutes = (
            standard_deviation_cross_course.kline_count * MAP_MINUTE_COUNT[standard_deviation_cross_course.interval]
        )
        standard_deviation_beta_spread_converted_to_minutes = (
            standard_deviation_beta_spread.kline_count * MAP_MINUTE_COUNT[standard_deviation_beta_spread.interval]
        )
        beta_factor_converted_to_minutes = (
            beta_factor.kline_count * MAP_MINUTE_COUNT[beta_factor.interval]
            + moving_average_beta_spread.kline_count * MAP_MINUTE_COUNT[moving_average_beta_spread.interval]
        )

        prepared_kline_max = max(
            moving_average_converted_to_minutes,
            standard_deviation_cross_course_converted_to_minutes,
            standard_deviation_beta_spread_converted_to_minutes,
            beta_factor_converted_to_minutes,
        )
        return start_time - timedelta(minutes=prepared_kline_max)

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

    def get_source_dfs(self) -> tuple:
        """ Возвращает 3 датафрейма со сдвигом start_time для всех индикаторов """

        prepared_start_time = self.get_qs_start_time(start_time=self.start_time)

        df_1 = self.get_symbol_df(
            symbol_pk=self.symbol_1_id,
            qs_start_time=prepared_start_time,
            qs_end_time=self.end_time,
        )
        df_2 = self.get_symbol_df(
            symbol_pk=self.symbol_2_id,
            qs_start_time=prepared_start_time,
            qs_end_time=self.end_time,
        )
        source_df = pd.DataFrame(columns=[
            'df_1',
            'df_2',
            'cross_course',
        ], dtype=float)

        source_df['df_1'] = df_1[self.price_comparison]
        source_df['df_2'] = df_2[self.price_comparison]
        source_df['cross_course'] = source_df['df_1'] / source_df['df_2']

        source_df = source_df.resample(self.interval).agg({
            'df_1': 'last',
            'df_2': 'last',
            'cross_course': 'last',
        })

        #  Cross course
        moving_average_cross_course = self.movingaverage_set.get(codename=self.ma_cross_course_codename)
        source_df[moving_average_cross_course.codename] = moving_average_cross_course.get_data(
            source_df=source_df,
            interval=self.interval,
        ).reindex(source_df.index, method='ffill')

        standard_deviation_cross_course = self.standarddeviation_set.get(codename=self.sd_cross_course_codename)
        source_df[standard_deviation_cross_course.codename] = standard_deviation_cross_course.get_data(
            source_df=source_df,
            interval=self.interval,
        ).reindex(source_df.index, method='ffill')

        source_df['ad_cross_course'] = (
                source_df['cross_course'] - source_df[moving_average_cross_course.codename].apply(Decimal)
        )
        source_df['sd_cross_course'] = (
                source_df['ad_cross_course'] / source_df[standard_deviation_cross_course.codename].apply(Decimal)
        )

        # Beta spread
        beta_factor = self.betafactor_set.first()
        source_df['beta'] = beta_factor.get_data(
            source_df=source_df,
            interval=self.interval,
        ).reindex(source_df.index, method='ffill')

        source_df['beta_spread'] = (
                source_df['df_1'] - source_df['df_2'] * source_df['beta'].apply(Decimal)
                if beta_factor.market_symbol == 'symbol_2' else
                source_df['df_2'] - source_df['df_1'] * source_df['beta'].apply(Decimal)
        )

        moving_average_beta_spread = self.movingaverage_set.get(codename=self.ma_beta_spread_codename)
        source_df[moving_average_beta_spread.codename] = moving_average_beta_spread.get_data(
            source_df=source_df,
            interval=self.interval,
        ).reindex(source_df.index, method='ffill')

        standard_deviation_beta_spread = self.standarddeviation_set.get(codename=self.sd_beta_spread_codename)
        source_df[standard_deviation_beta_spread.codename] = standard_deviation_beta_spread.get_data(
            source_df=source_df,
            interval=self.interval,
        ).reindex(source_df.index, method='ffill')

        source_df['ad_beta_spread'] = (
                source_df['beta_spread'] - source_df[moving_average_beta_spread.codename].apply(Decimal)
        )
        source_df['sd_beta_spread'] = (
                source_df['ad_beta_spread'] / source_df[standard_deviation_beta_spread.codename].apply(Decimal)
        )

        return df_1, df_2, source_df

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
