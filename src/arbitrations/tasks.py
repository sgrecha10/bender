from django.db import connection

from arbitrations.backends import ArbitrationBackend
from bender.celery_entry import app
from .models import Arbitration, ArbitrationDeal
from market_data.constants import AllowedInterval


@app.task(bind=True)
def run_arbitration_test_mode(self, arbitration_id: int):
    """ Запускаем арбитражную стратегию на тестовых данных """

    arbitration = Arbitration.objects.get(pk=arbitration_id)

    ArbitrationDeal.objects.filter(arbitration=arbitration).delete()

    if arbitration.entry_price_interval == AllowedInterval.MINUTE_1:
        query_params = [
            arbitration.symbol_1.symbol,
            arbitration.symbol_2.symbol,
            arbitration.start_time,
            arbitration.end_time,
        ]
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
        ORDER BY t1.open_time;
        """
    elif arbitration.entry_price_interval == AllowedInterval.DAY_1:
        query_params = [
            arbitration.symbol_1.symbol,  # для df1
            arbitration.symbol_1.symbol,  # для df1_open
            arbitration.symbol_1.symbol,  # для df1_close
            arbitration.symbol_2.symbol,  # для df2
            arbitration.symbol_2.symbol,  # для df2_open
            arbitration.symbol_2.symbol,  # для df2_close
            arbitration.start_time,  # начало диапазона
            arbitration.end_time,  # конец диапазона
        ]
        query = """
        WITH df1 AS (
            SELECT 
                DATE(open_time) AS day,
                MIN(open_time) AS first_time,
                MAX(open_time) AS last_time,
                MAX(high_price) AS high_price,
                MIN(low_price) AS low_price
            FROM market_data_kline
            WHERE symbol_id = %s
            GROUP BY DATE(open_time)
        ), df1_open AS (
            SELECT DATE(open_time) AS day, open_price, open_time
            FROM market_data_kline
            WHERE symbol_id = %s
        ), df1_close AS (
            SELECT DATE(open_time) AS day, close_price, open_time
            FROM market_data_kline
            WHERE symbol_id = %s
        ), t1 AS (
            SELECT 
                d.day,
                o.open_price,
                d.high_price,
                d.low_price,
                c.close_price
            FROM df1 d
            LEFT JOIN df1_open o ON d.day = o.day AND o.open_time = d.first_time
            LEFT JOIN df1_close c ON d.day = c.day AND c.open_time = d.last_time
        ), df2 AS (
            SELECT 
                DATE(open_time) AS day,
                MIN(open_time) AS first_time,
                MAX(open_time) AS last_time,
                MAX(high_price) AS high_price,
                MIN(low_price) AS low_price
            FROM market_data_kline
            WHERE symbol_id = %s
            GROUP BY DATE(open_time)
        ), df2_open AS (
            SELECT DATE(open_time) AS day, open_price, open_time
            FROM market_data_kline
            WHERE symbol_id = %s
        ), df2_close AS (
            SELECT DATE(open_time) AS day, close_price, open_time
            FROM market_data_kline
            WHERE symbol_id = %s
        ), t2 AS (
            SELECT 
                d.day,
                o.open_price,
                d.high_price,
                d.low_price,
                c.close_price
            FROM df2 d
            LEFT JOIN df2_open o ON d.day = o.day AND o.open_time = d.first_time
            LEFT JOIN df2_close c ON d.day = c.day AND c.open_time = d.last_time
        )
        
        SELECT 
            COALESCE(t1.day, t2.day) AS open_time,
            t1.open_price  AS df_1_open_price,
            t1.high_price  AS df_1_high_price,
            t1.low_price   AS df_1_low_price,
            t1.close_price AS df_1_close_price,
            t2.open_price  AS df_2_open_price,
            t2.high_price  AS df_2_high_price,
            t2.low_price   AS df_2_low_price,
            t2.close_price AS df_2_close_price
        FROM t1
        FULL OUTER JOIN t2 ON t1.day = t2.day
        WHERE COALESCE(t1.day, t2.day) BETWEEN %s AND %s
        ORDER BY open_time;
        """
    else:
        raise ValueError('Invalid entry_price_interval')

    def _fetch_large_data():
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                query_params,
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
