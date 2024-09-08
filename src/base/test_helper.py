import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import models

import market_data.constants as const
from market_data.models import ExchangeInfo, Interval, Kline
import pytz
from django.db.models import QuerySet


class TestHelperMixin:
    """Класс для создания тестовых сущностей"""

    def create_exchange_info(self,
                             symbol: str = None,
                             **kwargs) -> ExchangeInfo:
        return ExchangeInfo.objects.create(
            symbol=symbol if symbol else uuid.uuid4().hex,
            status='TRADING',
            **kwargs
        )

    def create_interval(self, codename: str = const.MINUTE_1, **kwargs) -> Interval:
        result, _ = Interval.objects.get_or_create(
            codename=codename,
            defaults={**kwargs},
        )
        return result

    def create_klines(self,
                     symbol: ExchangeInfo,
                     count: int = 1,
                     open_time: datetime = None,
                     **kwargs) -> list[Kline]:

        now = datetime.now().replace(second=0, microsecond=0, tzinfo=pytz.UTC)
        open_time = open_time if open_time else now

        bulk_data = []
        for i in range(count):
            close_time = open_time + timedelta(minutes=1) - timedelta(seconds=1)
            bulk_data.append(
                Kline(
                    symbol=symbol,
                    open_time=open_time,
                    open_price=20.0,
                    high_price=40.0,
                    low_price=10.0,
                    close_price=30.0,
                    volume=1000.0,
                    close_time=close_time,
                    **kwargs
                )
            )
            open_time -= timedelta(minutes=1)

        return Kline.objects.bulk_create(bulk_data)


    # def create_kline(self,
    #                  symbol: ExchangeInfo,
    #                  interval: Interval = None,
    #                  open_time: datetime = None,
    #                  open_price: Decimal | float = None,
    #                  high_price: Decimal | float = None,
    #                  low_price: Decimal | float = None,
    #                  close_price: Decimal | float = None,
    #                  volume: Decimal | float = None,
    #                  close_time: datetime = None,
    #                  **kwargs) -> Kline:
    #     now = datetime.now().replace(second=0, microsecond=0, tzinfo=pytz.UTC)
    #     open_time = open_time if open_time else now
    #     if not close_time:
    #         if not interval:
    #             interval = self.create_interval(IntervalCodename.MINUTE_1.name)
    #         close_time = open_time + timedelta(minutes=interval.minutes_count) - timedelta(seconds=1)
    #
    #     return Kline.objects.create(
    #         symbol=symbol,
    #         open_time=open_time,
    #         open_price=open_price if open_price else 20.0,
    #         high_price=high_price if high_price else 40.0,
    #         low_price=low_price if low_price else 10.0,
    #         close_price=close_price if close_price else 30.0,
    #         volume=volume if volume else 1000.0,
    #         close_time=close_time,
    #         **kwargs
    #     )
