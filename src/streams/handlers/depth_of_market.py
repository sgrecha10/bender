import time

from streams.models import TaskManagement
from streams.tasks import task_diff_book_depth
from core.clients.redis_client import RedisClient
from core.clients.binance.restapi import BinanceClient
from django.conf import settings
import requests
import logging
import json
from core.clients.kafka.kafka_client import KafkaConsumerClient


class WebSoketError(Exception):
    #  Сбой стакана
    pass

class DepthOfMarket:
    def __init__(self, logger: logging = None):
        self.is_start_to_redis = False  # флаг, устанавливается когда начинается запись стакана в Redis
        self.redis_conn = RedisClient()
        self.redis_conn.flushall()

        self.binance_client = BinanceClient(settings.BINANCE_CLIENT)
        self.kafka_client = KafkaConsumerClient()

        if not logger:
            self.logger = logging.getLogger(__name__)

    def run(self, symbol: str, depth: int = 100):
        self.logger.info(
            'Depth Of Market runned: symbol = %s, depth = %s', symbol, depth
        )

        if self._websocket_start(symbol):
            self.logger.info('Websocket started..')
            time.sleep(5)

        if last_update_id := self._get_snapshot(symbol, depth):
            self.logger.info('Snapshot received..')

            if self._process(last_update_id, symbol):
                self.logger.info('Process started.')

    def stop(self, symbol: str):
        if self._websocket_stop(symbol):
            self.logger.info(
                'Websocket stopped: symbol = %s', symbol
            )

    def _websocket_start(self, symbol: str):
        codename = f'diff_book_depth_{symbol}'.lower()
        task_management, _ = TaskManagement.objects.get_or_create(codename=codename)
        if task_management.is_working:
            # TODO LOG уже запущена
            return
        task_management.is_working = True
        task_management.save(update_fields=['is_working'])
        task_diff_book_depth.delay(symbol)

        return True

    def _websocket_stop(self, symbol: str):
        codename = f'diff_book_depth_{symbol}'.lower()
        try:
            task_management = TaskManagement.objects.get(codename=codename)
            task_management.is_working = False
            task_management.save(update_fields=['is_working'])
            return True
        except TaskManagement.DoesNotExist:
            return

    def _get_snapshot(self, symbol, depth) -> int | requests.ConnectionError:
        try:
            result, is_ok = self.binance_client.get_order_book(symbol, depth)
        except requests.ConnectionError as e:
            return e
        if is_ok:
            self._poll_redis(result, 'asks', 'ask')
            self._poll_redis(result, 'bids', 'bid')
        return result.get('lastUpdateId')

    def _consumer_message_handler(self, message, prev_message=None, last_update_id=None):
        # print(message, last_update_id)
        # print(f'grecha {message}')
        json_data = json.loads(message)
        # print(json_data)
        first_update = json_data.get('U')  # First update ID in event
        final_update = json_data.get('u')  # Final update ID in event

        if prev_message:
            prev_message_json_data = json.loads(prev_message)
        else:
            prev_message_json_data = {}

        prev_message_final_update = prev_message_json_data.get('u')

        if first_update and final_update:
            prepared_last_update_id = last_update_id + 1
            if first_update <= prepared_last_update_id <= final_update:
                self.is_start_to_redis = True
                self._poll_redis(json_data, 'a', 'ask')
                self._poll_redis(json_data, 'b', 'bid')

        if self.is_start_to_redis and prev_message_final_update and first_update == prev_message_final_update + 1:
            self._poll_redis(json_data, 'a', 'ask')
            self._poll_redis(json_data, 'b', 'bid')

        # raise WebSoketError('Depth Of Market failed!')

    def _process(self, last_update_id, symbol):
        self.kafka_client.get_topic(symbol, self._consumer_message_handler, last_update_id)

    def _poll_redis(self, data: dict, lookup_field: str, redis_key: str):
        print(data.get(lookup_field), lookup_field, redis_key)
        for item in data.get(lookup_field):
            price = item[0]
            if not float(item[1]):
                self.redis_conn.zremrangebyscore(redis_key, price, price)
            else:
                self.redis_conn.set_dom(redis_key, item)
