from arbitrations.backends import ArbitrationBackend
from bender.celery_entry import app
from market_data.models import Kline
from .models import Arbitration, ArbitrationDeal


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
        deal_time = open_time_1

        # выбираем порядок подачи тестовых цен на вход в стратегию
        entry_price_order_map = {
            Arbitration.EntryPriceOrder.MAXMIN: (
                (kline_1.high_price, kline_2.high_price),
                (kline_1.low_price, kline_2.low_price),
            ),
            Arbitration.EntryPriceOrder.MINMAX: (
                (kline_1.low_price, kline_2.low_price),
                (kline_1.high_price, kline_2.high_price),
            ),
            Arbitration.EntryPriceOrder.OPEN: (
                (kline_1.open_price, kline_2.open_price),
            ),
            Arbitration.EntryPriceOrder.CLOSE: (
                (kline_1.close_price, kline_2.close_price),
            ),
            Arbitration.EntryPriceOrder.HIGH: (
                (kline_1.high_price, kline_2.high_price),
            ),
            Arbitration.EntryPriceOrder.LOW: (
                (kline_1.low_price, kline_2.low_price),
            ),
        }

        for price_1, price_2 in entry_price_order_map.get(arbitration.entry_price_order, []):
            backend.run_step(
                price_1=price_1,
                price_2=price_2,
                deal_time=deal_time,
            )
