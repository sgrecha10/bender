import uuid
from datetime import datetime, timedelta

import pytz

import market_data.constants as const
from market_data.models import ExchangeInfo, Interval, Kline


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
