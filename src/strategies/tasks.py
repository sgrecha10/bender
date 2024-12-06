from bender.celery_entry import app
from .models import Strategy, StrategyResult
from .constants import CODENAME_MAP
from market_data.models import Kline
import random


@app.task(bind=True)
def run_strategy_test_mode(self, strategy_id: int):
    strategy = Strategy.objects.get(pk=strategy_id)

    StrategyResult.objects.filter(strategy=strategy).delete()

    # получаем бекенд стратегии
    backend = CODENAME_MAP[strategy.codename]()

    # получаем df для тестирования
    kline_df = Kline.objects.filter(
        symbol=strategy.base_symbol,
        open_time__gte=strategy.start_time,
        open_time__lte=strategy.end_time,
    ).group_by_interval().to_dataframe(index='open_time_group')

    # обходим полученный df начиная с самой старой свечи
    last_kline = None
    last_idx = None
    for idx, kline_item in kline_df.iterrows():
        price_data = [
            kline_item['high_price'],
            kline_item['low_price'],
            kline_item['open_price'],
            kline_item['close_price'],
        ]

        entry_price_order_map = {
            Strategy.EntryPriceOrder.MAXMIN: (0, 1),
            Strategy.EntryPriceOrder.MINMAX: (1, 0),
            Strategy.EntryPriceOrder.OPEN: (2,),
            Strategy.EntryPriceOrder.CLOSE: (3,),
            Strategy.EntryPriceOrder.HIGH: (0,),
            Strategy.EntryPriceOrder.LOW: (1,),
        }

        for item in entry_price_order_map.get(strategy.entry_price_order, []):
            backend.run_step(
                deal_time=idx,
                price=price_data[item],
            )

        last_kline = kline_item
        last_idx = idx

    backend.close_all_position(idx=last_idx, price=last_kline['close_price'])
