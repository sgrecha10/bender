import json
import time

from django.conf import settings

from bender.celery_entry import app
from core.clients.binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from core.clients.kafka.kafka_client import KafkaProducerClient
from core.clients.redis_client import RedisClient
from streams.models import TaskManagement


@app.task(bind=True)
def task_diff_book_depth(self, symbol: str):
    kafka_client = KafkaProducerClient(settings.KAFKA_CLIENT, topic=symbol)
    # redis_conn = RedisClient()
    # redis_conn.flushall()

    # def handler_message(_, message):
    #     json_data = json.loads(message)
    #
    #     group_prefix_bid = 'bid'
    #     bid_list = json_data['b']
    #     for item in bid_list:
    #         price = item[0]
    #         if not float(item[1]):
    #             redis_conn.zremrangebyscore(group_prefix_bid, price, price)
    #         else:
    #             redis_conn.set_dom(group_prefix_bid, item)
    #
    #     group_prefix_ask = 'ask'
    #     ask_list = json_data['a']
    #     for item in ask_list:
    #         price = item[0]
    #         if not float(item[1]):
    #             redis_conn.zremrangebyscore(group_prefix_ask, price, price)
    #         else:
    #             redis_conn.set_dom(group_prefix_ask, item)
    #
    #     # kafka_client.message_handler(_, message)

    my_client = SpotWebsocketStreamClient(on_message=kafka_client.message_handler)
    my_client.diff_book_depth(symbol=symbol)

    is_working = True
    while is_working:
        codename = f'diff_book_depth_{symbol}'.lower()
        is_working = TaskManagement.objects.only('is_working').get(codename=codename).is_working
        time.sleep(1)

    my_client.stop()
