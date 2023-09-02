from confluent_kafka import Consumer, OFFSET_BEGINNING, KafkaException
import socket
from django.conf import settings
from confluent_kafka import Producer
import json


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
        json_data = json.loads(message)
        print(json_data)

        self.producer.produce(
            topic=self.topic,
            value=message,
            # key=key,
            # on_delivery=callback,  # def callback(err, event):
        )
        self.producer.flush()


class KafkaConsumerClient:
    def __init__(self, credentials: dict):
        self.bootstrap_servers = credentials['bootstrap.servers']
        self.group_id = "hello_group"
        self.auto_offset_reset = 'smallest'
        self.enable_auto_commit = False

        self.consumer = Consumer(self.get_config())

    def get_config(self):
        return {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': self.auto_offset_reset,
            'enable.auto.commit': self.enable_auto_commit,
        }

    def get_topic(self):
        pass