from datetime import datetime
from typing import Optional

from django.conf import settings

from bender.celery_entry import app
from core.clients.binance.restapi import BinanceClient
from core.clients.binance.restapi.base import BinanceBaseRestClientException
from market_data.datetime_utils import datetime_to_timestamp, timestamp_to_datetime
from .models import Kline, ExchangeInfo


@app.task(bind=True)
def task_get_kline(self,
                   symbol: str,
                   interval: str,
                   start_time: Optional[datetime],
                   end_time: Optional[datetime],
                   limit: int):

    client = BinanceClient(settings.BINANCE_CLIENT)

    start_time = datetime_to_timestamp(start_time)
    end_time = datetime_to_timestamp(end_time)

    last_close_time = start_time

    while True:
        if (not last_close_time) or (end_time and last_close_time >= end_time):
            break

        result, is_ok = client.get_klines(
            symbol=symbol,
            interval=interval,
            start_time=last_close_time,
            end_time=end_time,
            limit=limit,
        )

        if not is_ok:
            raise BinanceBaseRestClientException(f'result: {result}, is_ok: {is_ok}')

        bulk_data = []
        for kline in result:
            close_time = timestamp_to_datetime(kline[6])
            bulk_data.append(
                Kline(
                    symbol=ExchangeInfo.objects.get(symbol=symbol),
                    open_time=timestamp_to_datetime(kline[0]),
                    open_price=kline[1],
                    high_price=kline[2],
                    low_price=kline[3],
                    close_price=kline[4],
                    volume=kline[5],
                    close_time=close_time,
                    quote_asset_volume=kline[7],
                    number_of_trades=kline[8],
                    taker_buy_base_asset_volume=kline[9],
                    taker_buy_quote_asset_volume=kline[10],
                    unused_field_ignore=kline[11],
                )
            )
        kline_list = Kline.objects.bulk_create(bulk_data, ignore_conflicts=True)

        last_kline = Kline.objects.filter(
            id__in=[item.id for item in kline_list],
        ).order_by('close_time').last()
        last_close_time = datetime_to_timestamp(last_kline.close_time) if last_kline else None

        print(last_close_time, end_time)

    return True
