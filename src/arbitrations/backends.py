from datetime import datetime
from decimal import Decimal
from arbitrations.models import Arbitration, ArbitrationDeal
import numpy as np
from market_data.constants import AllowedInterval


class ArbitrationBackend:

    def __init__(self, arbitration_id: int, **kwargs):
        self.arbitration = Arbitration.objects.get(pk=arbitration_id)
        # получаем df с рассчитанными характеристиками стратегии
        # arbitration_df = self.arbitration.get_df()
        # сдвигаем, что бы не высчитывать каждую итерацию предыдущий индекс
        self.arbitration_df = self.arbitration.get_df().shift(1)
        self.is_opened_deal = False

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

        moving_average_value = self.arbitration_df.loc[index, self.arbitration.moving_average.codename]
        standard_deviation_err = self.arbitration_df.loc[index, self.arbitration.standard_deviation.codename]

        if np.isnan(moving_average_value) or np.isnan(standard_deviation_err):
            return

        # определяем на сколько стандартных отклонений отличается кросс курс
        current_cross_curs = float(price_1 / price_2)
        standard_deviation = (current_cross_curs - moving_average_value) / standard_deviation_err

        # проверяем, что нужно открывать сделку
        if not self.is_opened_deal and abs(standard_deviation) >= float(self.arbitration.open_deal_sd):
            self.is_opened_deal = True
            # print('open')
            self._open_deal(
                price_1=price_1,
                price_2=price_2,
                deal_time=deal_time,
                is_first_buy=True,
            )

        # проверяем, что нужно закрывать сделку
        if self.is_opened_deal and abs(standard_deviation) <= float(self.arbitration.close_deal_sd):
            self.is_opened_deal = False
            # print('close')
            self._close_deal(
                price_1=price_1,
                price_2=price_2,
                deal_time=deal_time,
                is_first_buy=True,
            )

    def _open_deal(self, price_1: Decimal, price_2: Decimal, deal_time: datetime, is_first_buy: bool):
        ArbitrationDeal.objects.create(
            arbitration=self.arbitration,
            symbol=self.arbitration.symbol_1,
            deal_time=deal_time,
            buy=price_1,
            state=ArbitrationDeal.State.OPEN,
        )
        ArbitrationDeal.objects.create(
            arbitration=self.arbitration,
            symbol=self.arbitration.symbol_2,
            deal_time=deal_time,
            sell=price_2,
            state=ArbitrationDeal.State.OPEN,
        )

    def _close_deal(self, price_1: Decimal, price_2: Decimal, deal_time: datetime, is_first_buy: bool):
        ArbitrationDeal.objects.create(
            arbitration=self.arbitration,
            symbol=self.arbitration.symbol_1,
            deal_time=deal_time,
            sell=price_1,
            state=ArbitrationDeal.State.CLOSE,
        )
        ArbitrationDeal.objects.create(
            arbitration=self.arbitration,
            symbol=self.arbitration.symbol_2,
            deal_time=deal_time,
            buy=price_2,
            state=ArbitrationDeal.State.CLOSE,
        )
