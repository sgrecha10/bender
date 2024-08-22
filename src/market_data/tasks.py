from datetime import datetime, timezone
from typing import Optional

from django.conf import settings

from bender.celery_entry import app
from core.clients.binance.restapi import BinanceClient
from .models import Interval, ExchangeInfo, Kline


@app.task(bind=True)
def task_get_kline(self,
                   symbol: ExchangeInfo,
                   interval: Interval,
                   start_time: Optional[datetime],
                   end_time: Optional[datetime],
                   limit,
                   ):

    client = BinanceClient(settings.BINANCE_CLIENT)

    start_time = int(datetime.strftime(start_time, '%s')) * 1000 if start_time else None
    end_time = int(datetime.strftime(end_time, '%s')) * 1000 if end_time else None

    result, is_ok = client.get_klines(
        symbol=symbol.symbol,
        interval=interval.value,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )

    bulk_data = []
    for kline in result:
        bulk_data.append(
            Kline(
                symbol=symbol,
                open_time=datetime.fromtimestamp(kline[0]/1000, timezone.utc),
                open_price=kline[1],
                high_price=kline[2],
                low_price=kline[3],
                close_price=kline[4],
                volume=kline[5],
                close_time=datetime.fromtimestamp(kline[6]/1000, timezone.utc),
                quote_asset_volume=kline[7],
                number_of_trades=kline[8],
                taker_buy_base_asset_volume=kline[9],
                taker_buy_quote_asset_volume=kline[10],
                unused_field_ignore=kline[11],
            )
        )
    Kline.objects.bulk_create(bulk_data)
