from django.core.management import BaseCommand
from argparse import ArgumentParser, FileType

from confluent_kafka import Consumer, OFFSET_BEGINNING, KafkaException


class Command(BaseCommand):
    help = 'Consumer'

    def handle(self, *args, **options):
        config = {
            'bootstrap.servers': "kafka:9092",
            'group.id': "hello_group",
            'auto.offset.reset': 'smallest',
            'enable.auto.commit': False,
        }

        def assignment_callback(consumer, partitions):
            for p in partitions:
                print(f'Assigned to {p.topic}, partition {p.partition}')

        consumer = Consumer(config)
        consumer.subscribe(['hello_topic'], on_assign=assignment_callback)

        try:
            while True:
                event = consumer.poll(1.0)
                if event is None:
                    continue
                if event.error():
                    raise KafkaException(event.error())
                else:
                    val = event.value().decode('utf8')
                    partition = event.partition()
                    print(f'Received: {val} from partition {partition}    ')
                    consumer.commit(event)
        except KeyboardInterrupt:
            print('Canceled by user.')
        finally:
            consumer.close()
