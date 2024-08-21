import time

from django.conf import settings

from bender.celery_entry import app
from core.clients.binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from core.clients.kafka.kafka_client import KafkaProducerClient
from streams.models import TaskManagement
from .models import Interval, ExchangeInfo, Kline
from core.clients.binance.restapi.market_data import get_klines
from core.clients.binance.restapi import BinanceClient
from datetime import datetime, timedelta, timezone
from decimal import Decimal


@app.task(bind=True)
def task_get_kline(self,
                   symbol: ExchangeInfo,
                   interval: Interval,
                   start_time,
                   end_time,
                   limit,
                   ):
    print('grecha')
    client = BinanceClient(settings.BINANCE_CLIENT)

    start_time = datetime.strptime(start_time, '%d.%m.%Y %H:%M').strftime('%s000')
    end_time = datetime.strptime(end_time, '%d.%m.%Y %H:%M').strftime('%s000') if end_time != ' ' else None


    result, is_ok = client.get_klines(
        symbol=symbol.symbol,
        interval=interval.value,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    print(result)

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
