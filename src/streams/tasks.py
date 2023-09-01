import time

from django.conf import settings

from bender.celery_entry import app
from core.clients.binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from core.clients.kafka.kafka_client import KafkaProducerClient


@app.task(bind=True)
def task_diff_book_depth(self, symbol):
    kafka_client = KafkaProducerClient(settings.KAFKA_CLIENT)
    my_client = SpotWebsocketStreamClient(on_message=kafka_client.message_handler)
    my_client.diff_book_depth(symbol=symbol)
    time.sleep(10)
    my_client.stop()
