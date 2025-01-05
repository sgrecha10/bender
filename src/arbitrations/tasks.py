from bender.celery_entry import app
from .models import Arbitration, ArbitrationDeal
# from .constants import CODENAME_MAP
from market_data.models import Kline
import random
import numpy as np
from decimal import Decimal
from arbitrations.backends import ArbitrationBackend


@app.task(bind=True)
def run_arbitration_test_mode(self, arbitration_id: int):
    arbitration = Arbitration.objects.get(pk=arbitration_id)

    ArbitrationDeal.objects.filter(arbitration=arbitration).delete()

    # получаем qs для тестирования
    kline_qs_1 = Kline.objects.filter(
        symbol=arbitration.symbol_1,
        open_time__gte=arbitration.start_time,
        open_time__lte=arbitration.end_time,
    ).order_by('open_time')

    kline_qs_2 = Kline.objects.filter(
        symbol=arbitration.symbol_2,
        open_time__gte=arbitration.start_time,
        open_time__lte=arbitration.end_time,
    ).order_by('open_time')

    # получаем backend
    backend = ArbitrationBackend(arbitration_id=arbitration.id)

    # обходим одновременно оба qs
    for kline_1, kline_2 in zip(kline_qs_1, kline_qs_2):
        open_time_1 = kline_1.open_time
        open_time_2 = kline_2.open_time

        if open_time_1 != open_time_2:
            raise ValueError('Incorrect opening times')

        # цены, между которыми надо определять кросс курс. при тестировании Entry price order
        price_1 = kline_1.open_price
        price_2 = kline_2.open_price

        backend.run_step(price_1=price_1, price_2=price_2, deal_time=open_time_1)


    # # получаем бекенд стратегии
    # backend = CODENAME_MAP[strategy.codename]()
    #
    # # получаем df для тестирования
    # kline_df = Kline.objects.filter(
    #     symbol=strategy.base_symbol,
    #     open_time__gte=strategy.start_time,
    #     open_time__lte=strategy.end_time,
    # ).group_by_interval().to_dataframe(index='open_time_group')
    #
    # # обходим полученный df начиная с самой старой свечи
    # last_kline = None
    # last_idx = None
    # for idx, kline_item in kline_df.iterrows():
    #     price_data = [
    #         kline_item['high_price'],
    #         kline_item['low_price'],
    #         kline_item['open_price'],
    #         kline_item['close_price'],
    #     ]
    #
    #     entry_price_order_map = {
    #         Strategy.EntryPriceOrder.MAXMIN: (0, 1),
    #         Strategy.EntryPriceOrder.MINMAX: (1, 0),
    #         Strategy.EntryPriceOrder.OPEN: (2,),
    #         Strategy.EntryPriceOrder.CLOSE: (3,),
    #         Strategy.EntryPriceOrder.HIGH: (0,),
    #         Strategy.EntryPriceOrder.LOW: (1,),
    #     }
    #
    #     for item in entry_price_order_map.get(strategy.entry_price_order, []):
    #         backend.run_step(
    #             deal_time=idx,
    #             price=price_data[item],
    #         )
    #
    #     last_kline = kline_item
    #     last_idx = idx
    #
    # backend.close_all_position(idx=last_idx, price=last_kline['close_price'])
