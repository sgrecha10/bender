import json

import redis
from django.conf import settings


class RedisClient(redis.Redis):
    def __init__(self, db_number: int = 0):
        self.host = settings.REDIS_CLIENT['host']
        self.port = settings.REDIS_CLIENT['port']
        self.db_number = db_number
        super().__init__(
            host=self.host,
            port=self.port,
            db=int(self.db_number),
            decode_responses=True,
        )

    def set_dom(self, group_name: str, data: list):
        """
        :data:  [price, quantity]
        """
        price = float(data[0])
        quantity = float(data[1])
        item = json.dumps((price, quantity))
        self.zremrangebyscore(group_name, price, price)
        return self.zadd(group_name, {item: price})

    def get_dom_by_price(self, group_name:str, start: int = 0, end: int = -1, desc: bool = False):
        result = self.zrange(
            name=group_name,
            start=start,
            end=end,
            desc=desc,
        )
        return list(map(lambda x: json.loads(x), result))
