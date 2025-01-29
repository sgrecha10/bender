from django.db import models

from core.utils.db_utils import BaseModel
from indicators.models import MovingAverage, StandardDeviation
from market_data.models import Kline, ExchangeInfo
from market_data.constants import AllowedInterval, MAP_MINUTE_COUNT
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional, Type
import statsmodels.api as sm
import numpy as np


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
        choices=SymbolsRatioType.choices,
        default=SymbolsRatioType.PRICE,
        verbose_name='Ratio type',
        help_text='Определение соотношения инструментов на входе в сделку',
    )
    b_factor_window = models.PositiveIntegerField(
        default=1,
        verbose_name='B-factor size of window',
    )
    b_factor_price_comparison = models.CharField(
        choices=PriceComparison.choices,
        default=PriceComparison.CLOSE,
        verbose_name='B-factor price comparison',
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
        """ Рассчитывает start_time с учетом необходимого запаса для корректного расчета индикаторов """
        standard_deviation_kline_count = self.standard_deviation.kline_count if self.standard_deviation else 0
        moving_average_kline_count = self.moving_average.kline_count if self.moving_average else 0
        kline_max = max(
            standard_deviation_kline_count,
            moving_average_kline_count,
            self.b_factor_window,
        )
        computed_minutes_count = MAP_MINUTE_COUNT[self.interval]
        prepared_kline_max = kline_max * computed_minutes_count
        return start_time - timedelta(minutes=prepared_kline_max)

    def get_symbol_df(self,
                      symbol_pk: str | Type[int],
                      qs_start_time: Optional[datetime] = None,
                      qs_end_time: Optional[datetime] = None) -> pd.DataFrame:
        qs = Kline.objects.filter(symbol_id=symbol_pk)
        qs = qs.filter(open_time__gte=qs_start_time) if qs_start_time else qs
        qs = qs.filter(open_time__lte=qs_end_time) if qs_end_time else qs
        qs = qs.group_by_interval(self.interval)
        return qs.to_dataframe(index='open_time_group')

    def _get_df(self,
                df_1: pd.DataFrame,
                df_2: pd.DataFrame,
                start_time: datetime,
                end_time: datetime) -> pd.DataFrame:
        """Returned DataFrame"""
        moving_average = self.moving_average
        standard_deviation = self.standard_deviation

        df_cross_course = pd.DataFrame(columns=['cross_course'], dtype=float)
        df_cross_course['cross_course'] = df_1[self.price_comparison] / df_2[self.price_comparison]

        df_cross_course = df_cross_course.apply(pd.to_numeric, downcast='float')

        if moving_average:
            moving_average.calculate_values(df_cross_course, moving_average.codename)
            df_cross_course['absolute_deviation'] = (
                    df_cross_course['cross_course'] - df_cross_course[moving_average.codename]
            )

        if standard_deviation:
            standard_deviation.calculate_values(df_cross_course, standard_deviation.codename)
            df_cross_course['standard_deviation'] = (
                df_cross_course['absolute_deviation'] / df_cross_course[standard_deviation.codename]
            )

        df_cross_course = df_cross_course.loc[start_time:end_time]

        # все что ниже вывести в чарт, это исходники для расчета беты
        df_cross_course['variance_2'] = df_2[self.price_comparison].rolling(window=self.b_factor_window).var()

        df_covariance = pd.DataFrame(columns=['col_1', 'col_2'], dtype=float)
        df_covariance['col_1'] = df_1[self.b_factor_price_comparison]
        df_covariance['col_2'] = df_2[self.b_factor_price_comparison]

        df_covariance_matrix = df_covariance.rolling(
            window=self.b_factor_window,
        ).cov().dropna().unstack()['col_1']['col_2']

        df_cross_course['covariance'] = df_covariance_matrix

        df_cross_course['beta'] = df_cross_course['covariance'] / df_cross_course['variance_2']

        df_cross_course['beta_sm'] = self.rolling_beta(
            df_covariance['col_1'],
            df_covariance['col_2'],
            self.b_factor_window,
        )

        return df_cross_course

    # --- Функция для расчёта OLS ---
    def rolling_beta(self, y, x, window):
        """
        Рассчитывает коэффициент бета для скользящего окна.
        """
        n = len(y)  # Длина исходного ряда
        betas = []  # Список для сохранения бета-коэффициентов

        for start in range(n - window + 1):
            # Извлекаем окно данных
            y_window = y[start:start + window]
            x_window = x[start:start + window]

            # Удаляем NaN перед созданием модели
            valid_data = pd.concat([y_window, x_window], axis=1).dropna()

            # Если в окне нет данных, пропускаем
            if len(valid_data) == 0:
                betas.append(np.nan)
                continue

            # Извлекаем очищенные данные
            y_clean = valid_data.iloc[:, 0].values.astype(np.float64)  # Зависимая переменная
            x_clean = valid_data.iloc[:, 1].values.astype(np.float64)  # Независимая переменная

            # Добавляем константу для независимой переменной
            X = sm.add_constant(x_clean)

            # Строим модель
            model = sm.OLS(y_clean, X).fit()

            # Сохраняем коэффициент для X
            betas.append(model.params[1])

        # Добавляем NaN в начало (до первого окна) и в конец (до конца ряда)
        return betas[1:]
        # result = [np.nan] * (window - 1) + betas
        # result = result[:n]  # Обрезаем до длины DataFrame
        # return result

    def get_df(self, start_time: datetime = None, end_time: datetime = None) -> pd.DataFrame:
        start_time = start_time or self.start_time
        end_time = end_time or self.end_time

        qs_start_time = self.get_qs_start_time(start_time=start_time)

        df_1 = self.get_symbol_df(
            symbol_pk=self.symbol_1_id,
            qs_start_time=qs_start_time,
            qs_end_time=end_time,
        )
        df_2 = self.get_symbol_df(
            symbol_pk=self.symbol_2_id,
            qs_start_time=qs_start_time,
            qs_end_time=end_time,
        )
        return self._get_df(
            df_1=df_1,
            df_2=df_2,
            start_time=start_time,
            end_time=end_time,
        )


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
        ]

    def __str__(self):
        return self.arbitration.codename
