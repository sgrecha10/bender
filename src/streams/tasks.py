import time

from django.conf import settings

from bender.celery_entry import app
from core.clients.binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from core.clients.kafka.kafka_client import KafkaProducerClient
from streams.models import TaskManagement


@app.task(bind=True)
def task_diff_book_depth(self, symbol: str):
    kafka_client = KafkaProducerClient(settings.KAFKA_CLIENT, topic=symbol)
    my_client = SpotWebsocketStreamClient(on_message=kafka_client.message_handler)
    my_client.diff_book_depth(symbol=symbol)

    is_working = True
    while is_working:
        codename = f'diff_book_depth_{symbol}'.lower()
        is_working = TaskManagement.objects.only('is_working').get(codename=codename).is_working
        time.sleep(1)

    my_client.stop()
