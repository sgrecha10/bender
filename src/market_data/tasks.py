from datetime import datetime, timezone
from typing import Optional

from django.conf import settings

from bender.celery_entry import app
from core.clients.binance.restapi import BinanceClient
from .models import Interval, ExchangeInfo, Kline
from core.clients.binance.restapi.base import BinanceBaseRestClientException
from django.db import transaction
from market_data.datetime_utils import datetime_to_timestamp, timestamp_to_datetime


# @transaction.atomic()
@app.task(bind=True)
def task_get_kline(self,
                   symbol: ExchangeInfo,
                   interval: Interval,
                   start_time: Optional[datetime],
                   end_time: Optional[datetime],
                   limit,
                   ):

    client = BinanceClient(settings.BINANCE_CLIENT)

    start_time = datetime_to_timestamp(start_time)
    end_time = datetime_to_timestamp(end_time)

    last_close_time = start_time

    while True:
        result, is_ok = client.get_klines(
            symbol=symbol.symbol,
            interval=interval.value,
            start_time=last_close_time,
            end_time=end_time,
            limit=limit,
        )

        if not is_ok:
            raise BinanceBaseRestClientException(f'result: {result}, is_ok: {is_ok}')

        if last_close_time >= end_time:
            break

        bulk_data = []
        for kline in result:
            close_time = timestamp_to_datetime(kline[6])
            bulk_data.append(
                Kline(
                    symbol=symbol,
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
            # last_close_time = (int(datetime.strftime(close_time, '%s')) * 1000) + 1000
        kline_list = Kline.objects.bulk_create(bulk_data)
        last_kline = Kline.objects.filter(
            id__in=[item.id for item in kline_list],
        ).order_by('close_time').last()
        # last_kline = Kline.objects.order_by('id').last()
        last_close_time = datetime_to_timestamp(last_kline.close_time) + 1001

    return True
