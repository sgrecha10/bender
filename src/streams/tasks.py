import time

from django.conf import settings

from bender.celery_entry import app
from core.clients.binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from core.clients.kafka.kafka_client import KafkaProducerClient
from streams.models import TaskManagement


@app.task(bind=True)
def task_websoket_management(self, method: str, codename: str, *args, **kwargs):
    kafka_client = KafkaProducerClient(settings.KAFKA_CLIENT, topic=codename)
    my_client = SpotWebsocketStreamClient(on_message=kafka_client.message_handler)
    getattr(my_client, method)(*args, **kwargs)

    is_working = True
    while is_working:
        is_working = TaskManagement.objects.only('is_working').get(codename=codename).is_working
        time.sleep(1)

    my_client.stop()
