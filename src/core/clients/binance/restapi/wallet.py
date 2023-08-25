def get_capital_config_getall(client):
    urn = '/sapi/v1/capital/config/getall'
    method = 'GET'
    return client.sign_request(method, urn)


def get_trade_fee(client, symbol=None):
    urn = '/sapi/v1/asset/tradeFee'
    method = 'GET'
    payload = {'symbol': symbol}
    return client.sign_request(method, urn, payload)
