from django.core.management import BaseCommand
from argparse import ArgumentParser, FileType

from confluent_kafka import Consumer, OFFSET_BEGINNING


class Command(BaseCommand):
    help = 'Consumer'

    def handle(self, *args, **options):
        # Parse the command line.
        # parser = ArgumentParser()
        # parser.add_argument('config_file', type=FileType('r'))
        # parser.add_argument('--reset', action='store_true')
        # args = parser.parse_args()
        # print(parser)
        # return

        # Parse the configuration.
        # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
        # config_parser = ConfigParser()
        # config_parser.read_file(args.config_file)
        # config = dict(config_parser['default'])
        # config.update(config_parser['consumer'])

        config = {
            'bootstrap.servers': "kafka:9092",
            'group.id': "foo",
            'auto.offset.reset': 'smallest',
        }

        # Create Consumer instance
        consumer = Consumer(config)

        # Set up a callback to handle the '--reset' flag.
        def reset_offset(consumer, partitions):
            if True:
                for p in partitions:
                    p.offset = OFFSET_BEGINNING
                consumer.assign(partitions)

        # Subscribe to topic
        topic = "purchases"
        consumer.subscribe([topic], on_assign=reset_offset)

        # Poll for new messages from Kafka and print them.
        try:
            while True:
                msg = consumer.poll(0.1)
                if msg is None:
                    # Initial message consumption may take up to
                    # `session.timeout.ms` for the consumer group to
                    # rebalance and start consuming
                    print("Waiting...")
                elif msg.error():
                    print("ERROR: %s".format(msg.error()))
                else:
                    # Extract the (optional) key and value, and print.

                    print("Consumed event from topic {topic}: key = {key:12} value = {value:12}".format(
                        topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))
        except KeyboardInterrupt:
            pass
        finally:
            # Leave group and commit final offsets
            consumer.close()
