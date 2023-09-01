from django.core.management import BaseCommand
from random import choice
from confluent_kafka import Producer
import socket


class Command(BaseCommand):
    help = 'Producer'

    def handle(self, *args, **options):
        # Parse the configuration.
        # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
        # config_parser = ConfigParser()
        # config_parser.read_file(args.config_file)
        # config = dict(config_parser['default'])

        # Create Producer instance
        config = {
            'bootstrap.servers': "kafka:9092",
            'client.id': socket.gethostname(),
        }
        producer = Producer(config)

        # Optional per-message delivery callback (triggered by poll() or flush())
        # when a message has been successfully delivered or permanently
        # failed delivery (after retries).
        def delivery_callback(err, msg):
            if err:
                print('ERROR: Message failed delivery: {}'.format(err))
            else:
                print("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
                    topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

        # Produce data by selecting random values from these lists.
        topic = "purchases"
        user_ids = ['eabara', 'jsmith', 'sgarcia', 'jbernard', 'htanaka', 'awalther']
        products = ['book', 'alarm clock', 't-shirts', 'gift card', 'batteries']

        count = 0
        for _ in range(10):
            user_id = choice(user_ids)
            product = choice(products)
            producer.produce(topic, product, user_id, callback=delivery_callback)
            count += 1

        # Block until the messages are sent.
        producer.poll(10000)
        producer.flush()
