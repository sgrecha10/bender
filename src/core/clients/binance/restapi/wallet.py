# def get_status(self):
#     urn = '/sapi/v1/system/status'
#     method = 'GET'
#     data = {}
#
#     res, is_ok = self._request(data, urn, method)
#     return (res, True) if res['status'] == 0 else (res, False)
#
#
# def get_symbols(self):
#     urn = '/sapi/v1/margin/allPairs'
#     method = 'GET'
#     data = {}
#
#     return self._request(data, urn, method)


def get_capital_config_getall(self):
    urn = '/sapi/v1/capital/config/getall'
    method = 'GET'
    return self._sign_request(method, urn)


def get_trade_fee(self, symbol=None):
    urn = '/sapi/v1/asset/tradeFee'
    method = 'GET'
    payload = {'symbol': symbol}
    return self._sign_request(method, urn, payload)
