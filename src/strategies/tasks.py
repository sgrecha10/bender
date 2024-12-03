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
        price_data = [kline_item['high_price'], kline_item['low_price']]

        if strategy.entry_price_order == Strategy.EntryPriceOrder.MAXMIN:
            order_price_data = 0, 1

        elif strategy.entry_price_order == Strategy.EntryPriceOrder.MINMAX:
            order_price_data = 1, 0

        else:
            random_number = random.choice([0, 1])
            order_price_data = 0, 1 if random_number == 1 else 1, 0

        backend.run_step(
            deal_time=idx,
            price=price_data[order_price_data[0]],
        )
        backend.run_step(
            deal_time=idx,
            price=price_data[order_price_data[1]],
        )

        last_kline = kline_item
        last_idx = idx

    backend.close_all_position(idx=last_idx, price=last_kline['close_price'])
