import urllib.parse

from core.utils.value_utils import (
    clean_none_value,
    convert_list_to_json_array,
)


def get_exchange_info(client, symbol=None, symbols=None, permissions=None):
    method = 'GET'
    payload = {
        'symbol': symbol,
        'symbols': convert_list_to_json_array(symbols),
        'permissions': permissions,
    }
    params = urllib.parse.urlencode(clean_none_value(payload))
    urn = f'/api/v3/exchangeInfo?{params}'

    return client.send_request(method, urn, None)


def get_order_book(client, symbol=None, limit=100):
    method = 'GET'
    payload = {
        'symbol': symbol,
        'limit': int(limit),
    }
    params = urllib.parse.urlencode(clean_none_value(payload))
    urn = f'/api/v3/depth?{params}'

    return client.send_request(method, urn, None)


def get_klines(client, symbol=None, interval='1d', start_time=None, end_time=None, limit=1000):
    method = 'GET'
    payload = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_time,
        'endTime': end_time,
        'limit': int(limit),
    }
    params = urllib.parse.urlencode(clean_none_value(payload))
    urn = f'/api/v3/klines?{params}'

    return client.send_request(method, urn, None)
