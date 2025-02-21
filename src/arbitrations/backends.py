from datetime import datetime
from decimal import Decimal, ROUND_05UP

from django.db.models import Sum

from arbitrations.models import Arbitration, ArbitrationDeal
import numpy as np
from market_data.constants import AllowedInterval
from django.db.models.enums import IntegerChoices
from indicators.models import BetaFactor


class ArbitrationBackend:

    class DealState(IntegerChoices):
        CLOSED = 10
        OPENED_SYMBOL_FIRST_SELL = 20
        OPENED_SYMBOL_FIRST_BUY = 30

    def __init__(self, arbitration_id: int):
        self.arbitration = Arbitration.objects.get(pk=arbitration_id)

        # получаем df с рассчитанными характеристиками стратегии
        # arbitration_df = self.arbitration.get_df()
        # сдвигаем, что бы не высчитывать каждую итерацию предыдущий индекс
        # self.arbitration_df = self.arbitration.get_df().shift(1)
        _, _, cross_course = self.arbitration.get_source_dfs()
        self.arbitration_df = cross_course.shift(1)

        # состояние сделки
        self.deal_state = self.DealState.CLOSED

    def _prepare_index(self, deal_time: datetime) -> str:
        # приводим deal_time к размерности арбитражной стратегии (если arbitration.interval != 1m)
        if self.arbitration.interval == AllowedInterval.MINUTE_1:
            return str(deal_time)
        elif self.arbitration.interval == AllowedInterval.HOUR_1:
            return str(deal_time.replace(minute=0))
        elif self.arbitration.interval == AllowedInterval.DAY_1:
            return str(deal_time.replace(hour=0, minute=0))
        else:
            raise ValueError('Disallowed interval of arbitration')

    def run_step(self, price_1: Decimal, price_2: Decimal, deal_time: datetime):
        """ Получает цену 1 и 2 и timestamp, открывает/закрывает позицию
        :param price_1:
        :param price_2:
        :param deal_time:
        """

        # Приводим open_time к размерности арбитражной стратегии (если arbitration.interval != 1m)
        index = self._prepare_index(deal_time=deal_time)

        # Проверяем, открывать ли сделку по условию
        # if self.deal_state == self.DealState.CLOSED:
            # self._check_open_deal(price_1, price_2, index)

        # Проверяем, закрывать ли сделку по условию

        # Проверяем, закрывать ли сделку по временному stop-loss

        # Проверяем, корректировать ли размер  сделки




# class ArbitrationBackend:
#
#     class DealState(IntegerChoices):
#         CLOSED = 10
#         OPENED_SYMBOL_FIRST_SELL = 20
#         OPENED_SYMBOL_FIRST_BUY = 30
#
#     def __init__(self, arbitration_id: int, **kwargs):
#         self.arbitration = Arbitration.objects.get(pk=arbitration_id)
#
#         self.standard_deviation_cross_course = self.arbitration.standarddeviation_set.get(
#             codename=self.arbitration.sd_cross_course_codename,
#         )
#         self.moving_average_cross_course = self.arbitration.movingaverage_set.get(
#             codename=self.arbitration.ma_cross_course_codename,
#         )
#
#         self.beta_factor_model = self.arbitration.betafactor_set.first()
#         self.standard_deviation_beta_spread = self.arbitration.standarddeviation_set.get(
#             codename=self.arbitration.sd_beta_spread_codename,
#         )
#         self.moving_average_beta_spread = self.arbitration.movingaverage_set.get(
#             codename=self.arbitration.ma_beta_spread_codename,
#         )
#
#         # получаем df с рассчитанными характеристиками стратегии
#         # arbitration_df = self.arbitration.get_df()
#         # сдвигаем, что бы не высчитывать каждую итерацию предыдущий индекс
#         # self.arbitration_df = self.arbitration.get_df().shift(1)
#         _, _, cross_course = self.arbitration.get_source_dfs()
#         self.arbitration_df = cross_course.shift(1)
#
#         self.deal_state = self.DealState.CLOSED
#
#     def _prepare_index(self, deal_time: datetime) -> str:
#         # приводим deal_time к размерности арбитражной стратегии (если arbitration.interval != 1m)
#         if self.arbitration.interval == AllowedInterval.MINUTE_1:
#             return str(deal_time)
#         elif self.arbitration.interval == AllowedInterval.HOUR_1:
#             return str(deal_time.replace(minute=0))
#         elif self.arbitration.interval == AllowedInterval.DAY_1:
#             return str(deal_time.replace(hour=0, minute=0))
#         else:
#             raise ValueError('Disallowed interval of arbitration')
#
#     def _get_quantity(self, price_1, price_2, deal_time) -> tuple:
#         """Возвращает соотношение инструментов.
#
#         Используется при открытии сделки и при коррекции по бета.
#         """
#         symbol_1_quantity, symbol_2_quantity = 1, 1
#
#         ratio_type = self.arbitration.ratio_type
#         if ratio_type == self.arbitration.SymbolsRatioType.PRICE:
#             symbol_2_quantity = price_1 / price_2
#         elif ratio_type == self.arbitration.SymbolsRatioType.B_FACTOR:
#             index = self._prepare_index(deal_time=deal_time)
#             beta = self.arbitration_df.loc[index, 'beta']
#
#             if self.beta_factor_model.market_symbol == BetaFactor.MarketSymbol.SYMBOL_1:
#                 symbol_2_quantity = 1 / (beta + 1)
#                 symbol_1_quantity = 1 - symbol_2_quantity
#             elif self.beta_factor_model.market_symbol == BetaFactor.MarketSymbol.SYMBOL_2:
#                 symbol_1_quantity = 1 / (beta + 1)
#                 symbol_2_quantity = 1 - symbol_1_quantity
#             else:
#                 raise ValueError('BetaFactor.MarketSymbol не найден')
#
#         return (
#             Decimal(symbol_1_quantity).quantize(Decimal("1.0000000000"), ROUND_05UP),
#             Decimal(symbol_2_quantity).quantize(Decimal("1.0000000000"), ROUND_05UP),
#         )
#
#     def run_step(self, price_1: Decimal, price_2: Decimal, deal_time: datetime):
#         """ Получает цену 1 и 2 и timestamp, открывает/закрывает позицию
#
#         :param price_1:
#         :param price_2:
#         :param deal_time:
#         """
#
#         # приводим open_time к размерности арбитражной стратегии (если arbitration.interval != 1m)
#         index = self._prepare_index(deal_time=deal_time)
#
#         if self.arbitration.z_index == Arbitration.ZIndex.CROSS_COURSE:
#             moving_average_value = self.arbitration_df.loc[index, self.moving_average_cross_course.codename]
#             standard_deviation_err = self.arbitration_df.loc[index, self.standard_deviation_cross_course.codename]
#
#             if np.isnan(moving_average_value) or np.isnan(standard_deviation_err):
#                 return
#
#             # определяем на сколько стандартных отклонений отличается кросс курс
#             current_cross_curs = float(price_1 / price_2)
#             standard_deviation = (current_cross_curs - moving_average_value) / standard_deviation_err
#
#         elif self.arbitration.z_index == Arbitration.ZIndex.BETA_SPREAD:
#             beta_factor_value = self.arbitration_df.loc[index, 'beta']  # self.beta_factor_model.codename
#             moving_average_value = self.arbitration_df.loc[index, self.moving_average_beta_spread.codename]
#             standard_deviation_err = self.arbitration_df.loc[index, self.standard_deviation_beta_spread.codename]
#
#             beta_spread = (
#                 float(price_1) - float(price_2) * beta_factor_value
#                 if self.beta_factor_model.market_symbol == 'symbol_2' else
#                 float(price_2) - float(price_1) * beta_factor_value
#             )
#             standard_deviation = - (beta_spread - moving_average_value) / standard_deviation_err
#
#         else:
#             raise ValueError('ZIndex does not exist.')
#
#         # проверяем, что нужно открывать сделку
#         if (self.deal_state == self.DealState.CLOSED
#                 and abs(standard_deviation) >= float(self.arbitration.open_deal_sd)):
#             # print('open')
#             self._open_deal(
#                 price_1=price_1,
#                 price_2=price_2,
#                 deal_time=deal_time,
#                 standard_deviation=standard_deviation,
#             )
#
#         # проверяем, что нужно закрывать сделку
#         if (self.deal_state != self.DealState.CLOSED
#                 and abs(standard_deviation) <= float(self.arbitration.close_deal_sd)):
#             # print('close')
#             self._close_deal(
#                 price_1=price_1,
#                 price_2=price_2,
#                 deal_time=deal_time,
#             )
#
#         # проверяем, что нужна коррекция позиции (по бете)
#         if (self.deal_state != self.DealState.CLOSED
#                 and abs(standard_deviation) > float(self.arbitration.close_deal_sd)):
#             # print('correction')
#             if self.arbitration.correction_type == Arbitration.CorrectionType.EVERY_TIME:
#                 self._correction_deal(
#                     price_1=price_1,
#                     price_2=price_2,
#                     deal_time=deal_time,
#                     standard_deviation=standard_deviation,
#                 )
#
#         # временной стоп-лосс
#         pass
#
#     def _open_deal(self, price_1: Decimal, price_2: Decimal, deal_time: datetime, standard_deviation: Decimal):
#         """ Открываем сделку
#
#         :param price_1:
#         :param price_2:
#         :param deal_time:
#         :param standard_deviation: для определения в какую сторону открываться
#         """
#
#         data = {
#             'arbitration': self.arbitration,
#             'deal_time': deal_time,
#             'state': ArbitrationDeal.State.OPEN,
#         }
#
#         symbol_1_quantity, symbol_2_quantity = self._get_quantity(
#             price_1=price_1,
#             price_2=price_2,
#             deal_time=deal_time,
#         )
#
#         if standard_deviation > 0:
#             ArbitrationDeal.objects.create(
#                 symbol=self.arbitration.symbol_1,
#                 price=price_1,
#                 quantity=symbol_1_quantity,
#                 **data,
#             )
#             ArbitrationDeal.objects.create(
#                 symbol=self.arbitration.symbol_2,
#                 price=price_2,
#                 quantity=-symbol_2_quantity,
#                 **data,
#             )
#             self.deal_state = self.DealState.OPENED_SYMBOL_FIRST_SELL
#
#         elif standard_deviation < 0:
#             ArbitrationDeal.objects.create(
#                 symbol=self.arbitration.symbol_1,
#                 price=price_1,
#                 quantity=-symbol_1_quantity,
#                 **data,
#             )
#             ArbitrationDeal.objects.create(
#                 symbol=self.arbitration.symbol_2,
#                 price=price_2,
#                 quantity=symbol_2_quantity,
#                 **data,
#             )
#             self.deal_state = self.DealState.OPENED_SYMBOL_FIRST_BUY
#
#     def _get_quantity_from_db(self) -> tuple:
#         """ Возвращает количество инструментов в последней сделке
#
#         как определить текущую сделку?
#         сортирую таблицу от последнего к первому
#         фильтрую по state=ArbitrationDeal.State.OPEN
#
#         """
#         # получаем точки входа в сделку
#         symbol_1_deal = ArbitrationDeal.objects.filter(
#             arbitration=self.arbitration,
#             symbol=self.arbitration.symbol_1,
#             state=ArbitrationDeal.State.OPEN,
#         ).order_by('-deal_time')[0]
#         symbol_2_deal = ArbitrationDeal.objects.filter(
#             arbitration=self.arbitration,
#             symbol=self.arbitration.symbol_2,
#             state=ArbitrationDeal.State.OPEN,
#         ).order_by('-deal_time')[0]
#
#         # суммируем количества с учетом знака
#         symbol_1_quantity = ArbitrationDeal.objects.filter(
#             arbitration=self.arbitration,
#             symbol=self.arbitration.symbol_1,
#             deal_time__gte=symbol_1_deal.deal_time,
#         ).aggregate(sum=Sum('quantity'))['sum']
#         symbol_2_quantity = ArbitrationDeal.objects.filter(
#             arbitration=self.arbitration,
#             symbol=self.arbitration.symbol_2,
#             deal_time__gte=symbol_2_deal.deal_time,
#         ).aggregate(sum=Sum('quantity'))['sum']
#
#         return symbol_1_quantity, symbol_2_quantity
#
#     def _close_deal(self, price_1: Decimal, price_2: Decimal, deal_time: datetime):
#         """ Закрываем сделку
#
#         :param price_1:
#         :param price_2:
#         :param deal_time:
#         """
#
#         # получаем суммарное количество открытых позиций в сделке по каждому инструменту
#         symbol_1_quantity, symbol_2_quantity = self._get_quantity_from_db()
#
#         ArbitrationDeal.objects.create(
#             symbol=self.arbitration.symbol_1,
#             price=price_1,
#             quantity=-symbol_1_quantity,
#             arbitration=self.arbitration,
#             deal_time=deal_time,
#             state=ArbitrationDeal.State.CLOSE,
#         )
#         ArbitrationDeal.objects.create(
#             symbol=self.arbitration.symbol_2,
#             price=price_2,
#             quantity=-symbol_2_quantity,
#             arbitration=self.arbitration,
#             deal_time=deal_time,
#             state=ArbitrationDeal.State.CLOSE,
#         )
#         self.deal_state = self.DealState.CLOSED
#
#     def _correction_deal(self, price_1: Decimal, price_2: Decimal, deal_time: datetime, standard_deviation: Decimal):
#         """Корректируем сделку по бете
#
#         :param price_1:
#         :param price_2:
#         :param deal_time:
#         :param standard_deviation:
#         """
#         if self.arbitration.ratio_type != self.arbitration.SymbolsRatioType.B_FACTOR:
#             return
#
#         data = {
#             'arbitration': self.arbitration,
#             'deal_time': deal_time,
#             'state': ArbitrationDeal.State.CORRECTION,
#         }
#
#         # получаем количество инструментов по текущей бете
#         beta_symbol_1_quantity, beta_symbol_2_quantity = self._get_quantity(price_1, price_2, deal_time)
#
#         # получаем текущее количество инструментов в сделке
#         db_symbol_1_quantity, db_symbol_2_quantity = self._get_quantity_from_db()
#
#         # считаем на сколько нужно изменить количество инструментов
#         if db_symbol_1_quantity > 0:
#             dt_symbol_1_quantity = beta_symbol_1_quantity - db_symbol_1_quantity
#         elif db_symbol_1_quantity < 0:
#             dt_symbol_1_quantity = - (beta_symbol_1_quantity + db_symbol_1_quantity)
#         else:
#             dt_symbol_1_quantity = Decimal(0)
#
#         if db_symbol_2_quantity > 0:
#             dt_symbol_2_quantity = beta_symbol_2_quantity - db_symbol_2_quantity
#         elif db_symbol_2_quantity < 0:
#             dt_symbol_2_quantity = - (beta_symbol_2_quantity + db_symbol_2_quantity)
#         else:
#             dt_symbol_2_quantity = Decimal(0)
#
#         if dt_symbol_1_quantity:
#             ArbitrationDeal.objects.create(
#                 symbol=self.arbitration.symbol_1,
#                 price=price_1,
#                 quantity=dt_symbol_1_quantity,
#                 beta_quantity_1=beta_symbol_1_quantity,
#                 beta_quantity_2=beta_symbol_2_quantity,
#                 **data,
#             )
#
#         if dt_symbol_2_quantity:
#             ArbitrationDeal.objects.create(
#                 symbol=self.arbitration.symbol_2,
#                 price=price_2,
#                 quantity=dt_symbol_2_quantity,
#                 beta_quantity_1=beta_symbol_1_quantity,
#                 beta_quantity_2=beta_symbol_2_quantity,
#                 **data,
#             )
