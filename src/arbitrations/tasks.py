from django.db import connection

from arbitrations.backends import ArbitrationBackend
from bender.celery_entry import app
from .models import Arbitration, ArbitrationDeal


@app.task(bind=True)
def run_arbitration_test_mode(self, arbitration_id: int):
    """ Запускаем арбитражную стратегию на тестовых данных """

    arbitration = Arbitration.objects.get(pk=arbitration_id)

    ArbitrationDeal.objects.filter(arbitration=arbitration).delete()

    query = """
    SELECT 
        t1.open_time,
        t1.open_price  AS df_1_open_price,
        t1.high_price  AS df_1_high_price,
        t1.low_price   AS df_1_low_price,
        t1.close_price AS df_1_close_price,
        t2.open_price  AS df_2_open_price,
        t2.high_price  AS df_2_high_price,
        t2.low_price   AS df_2_low_price,
        t2.close_price AS df_2_close_price
    FROM 
        (SELECT * FROM market_data_kline WHERE symbol_id = %s) t1
    FULL JOIN 
        (SELECT * FROM market_data_kline WHERE symbol_id = %s) t2
    ON t1.open_time = t2.open_time
    WHERE t1.open_time BETWEEN %s AND %s
    ORDER BY t1.open_time
    LIMIT 10;
    """

    def _fetch_large_data():
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                [
                    arbitration.symbol_1.symbol,
                    arbitration.symbol_2.symbol,
                    arbitration.start_time,
                    arbitration.end_time,
                ],
            )
            columns = [col[0] for col in cursor.description]  # Получаем имена колонок
            for item in cursor:  # Генераторная итерация
                yield dict(zip(columns, item))  # Возвращаем по одной строке как dict


    # получаем backend
    backend = ArbitrationBackend(arbitration_id=arbitration.id)

    for row in _fetch_large_data():
        # выбираем порядок подачи тестовых цен на вход в стратегию
        entry_price_order_map = {
            Arbitration.EntryPriceOrder.MAXMIN: (
                (row['df_1_high_price'], row['df_2_high_price']),
                (row['df_1_low_price'], row['df_2_low_price']),
            ),
            Arbitration.EntryPriceOrder.MINMAX: (
                (row['df_1_low_price'], row['df_2_low_price']),
                (row['df_1_high_price'], row['df_2_high_price']),
            ),
            Arbitration.EntryPriceOrder.OPEN: (
                (row['df_1_open_price'], row['df_2_open_price']),
            ),
            Arbitration.EntryPriceOrder.CLOSE: (
                (row['df_1_close_price'], row['df_2_close_price']),
            ),
            Arbitration.EntryPriceOrder.HIGH: (
                (row['df_1_high_price'], row['df_2_high_price']),
            ),
            Arbitration.EntryPriceOrder.LOW: (
                (row['df_1_low_price'], row['df_2_low_price']),
            ),
        }

        for price_1, price_2 in entry_price_order_map.get(arbitration.entry_price_order, []):
            # print(price_1, price_2)
            backend.run_step(
                price_1=price_1,
                price_2=price_2,
                deal_time=row['open_time'],
            )
