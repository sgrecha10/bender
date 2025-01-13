from datetime import datetime
from decimal import Decimal
from arbitrations.models import Arbitration, ArbitrationDeal
import numpy as np
from market_data.constants import AllowedInterval
from django.db.models.enums import IntegerChoices


class ArbitrationBackend:

    class DealState(IntegerChoices):
        CLOSED = 10
        OPENED_SYMBOL_FIRST_SELL = 20
        OPENED_SYMBOL_FIRST_BUY = 30

    def __init__(self, arbitration_id: int, **kwargs):
        self.arbitration = Arbitration.objects.get(pk=arbitration_id)
        # получаем df с рассчитанными характеристиками стратегии
        # arbitration_df = self.arbitration.get_df()
        # сдвигаем, что бы не высчитывать каждую итерацию предыдущий индекс
        self.arbitration_df = self.arbitration.get_df().shift(1)
        self.deal_state = self.DealState.CLOSED

    def _prepare_index(self, deal_time: datetime) -> str:
        # приводим open_time к размерности арбитражной стратегии (если arbitration.interval != 1m)
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

        # приводим open_time к размерности арбитражной стратегии (если arbitration.interval != 1m)
        if self.arbitration.interval == AllowedInterval.MINUTE_1:
            index = str(deal_time)
        elif self.arbitration.interval == AllowedInterval.HOUR_1:
            index = str(deal_time.replace(minute=0))
        elif self.arbitration.interval == AllowedInterval.DAY_1:
            index = str(deal_time.replace(hour=0, minute=0))
        else:
            raise ValueError('Disallowed interval of arbitration')

        index = self._prepare_index(deal_time=deal_time)

        moving_average_value = self.arbitration_df.loc[index, self.arbitration.moving_average.codename]
        standard_deviation_err = self.arbitration_df.loc[index, self.arbitration.standard_deviation.codename]

        if np.isnan(moving_average_value) or np.isnan(standard_deviation_err):
            return

        # определяем на сколько стандартных отклонений отличается кросс курс
        current_cross_curs = float(price_1 / price_2)
        standard_deviation = (current_cross_curs - moving_average_value) / standard_deviation_err

        # проверяем, что нужно открывать сделку
        if (self.deal_state == self.DealState.CLOSED
                and abs(standard_deviation) >= float(self.arbitration.open_deal_sd)):
            # print('open')
            self._open_deal(
                price_1=price_1,
                price_2=price_2,
                deal_time=deal_time,
                standard_deviation=standard_deviation,
            )

        # проверяем, что нужно закрывать сделку
        if (self.deal_state != self.DealState.CLOSED
                and abs(standard_deviation) <= float(self.arbitration.close_deal_sd)):
            # print('close')
            self._close_deal(
                price_1=price_1,
                price_2=price_2,
                deal_time=deal_time,
            )

    def _get_quantity(self, price_1, price_2, deal_time) -> tuple:
        symbol_1_quantity, symbol_2_quantity = 1, 1

        ratio_type = self.arbitration.ratio_type
        if ratio_type == self.arbitration.SymbolsRatioType.PRICE:
            symbol_2_quantity = price_1 / price_2
        elif ratio_type == self.arbitration.SymbolsRatioType.B_FACTOR:
            index = self._prepare_index(deal_time=deal_time)
            beta = self.arbitration_df.loc[index, 'beta']
            symbol_2_quantity = 1 / (beta + 1)
            symbol_1_quantity = 1 - symbol_2_quantity

        return symbol_1_quantity, symbol_2_quantity

    def _open_deal(self, price_1: Decimal, price_2: Decimal, deal_time: datetime, standard_deviation: Decimal):
        data = {
            'arbitration': self.arbitration,
            'deal_time': deal_time,
            'state': ArbitrationDeal.State.OPEN,
        }

        symbol_1_quantity, symbol_2_quantity = self._get_quantity(
            price_1=price_1,
            price_2=price_2,
            deal_time=deal_time,
        )
        # symbol_2_quantity = self._get_quantity(symbol=self.arbitration.symbol_2, price_1=price_1, price_2=price_2)

        if float(standard_deviation) >= 0:
            ArbitrationDeal.objects.create(
                symbol=self.arbitration.symbol_1,
                sell=price_1,
                quantity=symbol_1_quantity,
                **data,
            )
            ArbitrationDeal.objects.create(
                symbol=self.arbitration.symbol_2,
                buy=price_2,
                quantity=symbol_2_quantity,
                **data,
            )
            self.deal_state = self.DealState.OPENED_SYMBOL_FIRST_SELL
        else:
            ArbitrationDeal.objects.create(
                symbol=self.arbitration.symbol_1,
                buy=price_1,
                quantity=symbol_1_quantity,
                **data,
            )
            ArbitrationDeal.objects.create(
                symbol=self.arbitration.symbol_2,
                sell=price_2,
                quantity=symbol_2_quantity,
                **data,
            )
            self.deal_state = self.DealState.OPENED_SYMBOL_FIRST_BUY

    def _close_deal(self, price_1: Decimal, price_2: Decimal, deal_time: datetime):
        open_deal_qs = ArbitrationDeal.objects.filter(
            state=ArbitrationDeal.State.OPEN,
        ).order_by('-deal_time')[:2]

        buy = sell = None
        for open_deal in open_deal_qs:
            if open_deal.sell:
                buy = price_1 if open_deal.symbol == self.arbitration.symbol_1 else price_2
                sell = None
            elif open_deal.buy:
                buy = None
                sell = price_1 if open_deal.symbol == self.arbitration.symbol_1 else price_2

            ArbitrationDeal.objects.create(
                symbol=open_deal.symbol,
                sell=sell,
                buy=buy,
                quantity=open_deal.quantity,
                arbitration=self.arbitration,
                deal_time=deal_time,
                state=ArbitrationDeal.State.CLOSE,
            )

        self.deal_state = self.DealState.CLOSED
