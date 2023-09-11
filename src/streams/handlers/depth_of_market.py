import json
import logging
import time

import requests
from django.conf import settings

from core.clients.binance.restapi import BinanceClient
from core.clients.kafka.kafka_client import (
    KafkaProducerClient,
    KafkaConsumerClient,
)
from core.clients.redis_client import RedisClient
from streams.models import TaskManagement
from streams.tasks import task_websoket_management


class DepthOfMarketStreamError(Exception):
    def __init__(self, msg):
        self.msg = msg


class DepthOfMarketStream:
    def __init__(self, symbol: str, depth: int, logger: logging = None):
        self.symbol = symbol
        self.depth = depth

        self.codename_websocket_task = f'diff_book_depth_{symbol}_{depth}'

        self.is_start_to_redis = False  # флаг, устанавливается когда начинается запись стакана в Redis
        self.redis_conn = RedisClient()
        self.redis_conn.flushall()

        self.binance_client = BinanceClient()
        self.kafka_consumer_client = KafkaConsumerClient()
        self.kafka_producer_client = KafkaProducerClient(topic=self.codename_websocket_task)

        if not logger:
            self.logger = logging.getLogger(__name__)

    def run(self):
        self._websocket_start()
        time.sleep(1)

        if last_update_id := self._get_snapshot():
            print(last_update_id)
        #     self._process(last_update_id, symbol)

    def stop(self):
        self._websocket_stop()

    def _websocket_start(self):
        task_management, _ = TaskManagement.objects.get_or_create(codename=self.codename_websocket_task)
        if task_management.is_working:
            raise DepthOfMarketStreamError(f'Websocket уже запущен, codename = {self.codename_websocket_task}')
        task_management.is_working = True
        task_management.save(update_fields=['is_working'])
        task_websoket_management.delay('diff_book_depth', self.codename_websocket_task, symbol=self.symbol)

        self.logger.info('Websocket is running: codename = %s', self.codename_websocket_task)
        return True

    def _websocket_stop(self):
        try:
            task_management = TaskManagement.objects.get(codename=self.codename_websocket_task)
            task_management.is_working = False
            task_management.save(update_fields=['is_working'])
        except TaskManagement.DoesNotExist:
            raise DepthOfMarketStreamError(f'Websocket не найден, codename = {self.codename_websocket_task}')

        self.logger.info('Websocket stopped: codename = %s', self.codename_websocket_task)
        return True

    def _get_snapshot(self) -> int | DepthOfMarketStreamError:
        try:
            result, is_ok = self.binance_client.get_order_book(self.symbol, self.depth)
        except requests.ConnectionError as e:
            raise DepthOfMarketStreamError(f'Snapshot не получен. Error: {e}')

        if is_ok:
            self.kafka_producer_client.message_handler(None, message=result)
            self.logger.info('Snapshot received: codename = %s', self.codename_websocket_task)
            return result.get('lastUpdateId')

        raise DepthOfMarketStreamError('Snapshot не получен, is_ok = False')


        # if is_ok:
        #     self._poll_redis(result, 'asks', 'ask')
        #     self._poll_redis(result, 'bids', 'bid')



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
        self.kafka_consumer_client.get_topic(symbol, self._consumer_message_handler, last_update_id)

    def _poll_redis(self, data: dict, lookup_field: str, redis_key: str):
        print(data.get(lookup_field), lookup_field, redis_key)
        for item in data.get(lookup_field):
            price = item[0]
            if not float(item[1]):
                self.redis_conn.zremrangebyscore(redis_key, price, price)
            else:
                self.redis_conn.set_dom(redis_key, item)
