import redis
from django.conf import settings


class RedisClient:
    def __init__(self, credentials: dict):
        self.host = credentials['host']
        self.port = credentials['port']

    def get_pool_connection(self, db_number: int = 0):
        return redis.Redis(
            host=self.host,
            port=self.port,
            db=int(db_number),
            decode_responses=True,
        )


redis_client = RedisClient(settings.REDIS_CLIENT)
