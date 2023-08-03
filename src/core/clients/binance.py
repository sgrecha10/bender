from typing import Tuple

import requests


class BinanceClient:
    def __init__(self, credentials: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uri = credentials['uri']
        self.api_key = credentials['api_key']
        # self.secret_key = credentials['secret_key']
        # self.hmac = credentials['hmac']

    def _request(self, data: dict, urn: str, method: str) -> Tuple[dict, bool]:
        with requests.Session() as session:
            headers = {
                'X-MBX-APIKEY': self.api_key,
            }

            session.headers.update(headers)

            res = session.request(
                method=method,
                url=self.uri + urn,
                data=data,
            )
            json_data = res.json()

            return (
                (json_data, True)
                if res.status_code == 200
                else (json_data, False)
            )

    def ping(self):
        urn = '/api/v3/ping'
        method = 'GET'
        data = {}

        return self._request(data, urn, method)

    def get_symbols(self):
        urn = '/sapi/v1/margin/allPairs'
        method = 'GET'
        data = {}

        return self._request(data, urn, method)

    def _prepare_data(self):
        pass
