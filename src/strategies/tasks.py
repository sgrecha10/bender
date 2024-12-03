from bender.celery_entry import app
from .models import Strategy, StrategyResult
from .constants import CODENAME_MAP
from market_data.models import Kline


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
        # потому что тестирование
        backend.run_step(
            deal_time=idx,
            price=kline_item['high_price'],
        )
        backend.run_step(
            deal_time=idx,
            price=kline_item['low_price'],
        )
        last_kline = kline_item
        last_idx = idx

    backend.close_all_position(idx=last_idx, price=last_kline['close_price'])
