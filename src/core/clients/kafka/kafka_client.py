import logging
import socket

from confluent_kafka import Consumer
from confluent_kafka import Producer
from django.conf import settings


class KafkaProducerClient:
    def __init__(self, credentials: dict, topic: str = None):
        self.bootstrap_servers = credentials['bootstrap.servers']
        self.client_id = socket.gethostname(),
        self.topic = topic if topic else 'default'

        self.producer = Producer(self.get_config())

    def get_config(self):
        return {
            'bootstrap.servers': self.bootstrap_servers,
            'client.id': self.client_id,
        }

    def message_handler(self, _, message):
        # json_data = json.loads(message)
        # print(json_data)

        self.producer.produce(
            topic=self.topic,
            value=message,  # str, byte
            # key=key,
            # on_delivery=callback,  # def callback(err, event):
        )
        self.producer.flush()


class KafkaConsumerClient:  # ЭТО НАДО ВЫЗЫВАТЬ В НОВОЙ ТАСКЕ
    def __init__(self, logger=None):
        self.bootstrap_servers = settings.KAFKA_CLIENT['bootstrap.servers']
        self.group_id = "hello_group"
        self.auto_offset_reset = 'smallest'
        self.enable_auto_commit = False

        self.consumer = Consumer(self.get_config())

        if not logger:
            self.logger = logging.getLogger(__name__)

    def get_config(self):
        return {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': self.auto_offset_reset,
            'enable.auto.commit': self.enable_auto_commit,
        }

    def get_topic(self, topic: str, message_handler, *args, **kwargs):
        self.consumer.subscribe([topic])
        try:
            prev_message = None
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    self.logger.info('Empty message')
                elif msg.error():
                    self.logger.info("ERROR: %s".format(msg.error()))
                else:
                    message = msg.value().decode('utf-8')
                    message_handler(message, prev_message, *args, **kwargs)
                    prev_message = message
        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()
