import urllib.parse

from core.utils.value_utils import clean_none_value


def get_exchange_info(client, symbol=None, symbols=None, permissions=None):
    method = 'GET'
    payload = {
        'symbol': symbol,
        'symbols': symbols,
        'permissions': permissions,
    }
    params = urllib.parse.urlencode(clean_none_value(payload))
    urn = f'/api/v3/exchangeInfo?{params}'

    return client.send_request(method, urn, None)
