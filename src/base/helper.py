import uuid
from datetime import timedelta

from django.utils import timezone

from market_data.models import ExchangeInfo, Kline


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

    def create_klines(self,
                     symbol: ExchangeInfo | str,
                     count: int = 1,
                     **kwargs) -> list[Kline]:

        open_time = timezone.now().replace(second=0, microsecond=0)  # now

        bulk_data = []
        for i in range(count):
            close_time = open_time + timedelta(seconds=59)
            bulk_data.append(
                Kline(
                    symbol_id=str(symbol),
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
