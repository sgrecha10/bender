import hashlib
import hmac
import time
from typing import Tuple
from urllib.parse import urlencode

import requests


class BinanceClient:
    timeout = 1

    def __init__(self, credentials: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.uri = credentials['uri']
        self.api_key = credentials['api_key']
        self.secret_key = credentials['secret_key']

    @staticmethod
    def _get_timestamp():
        return int(time.time() * 1000)

    @staticmethod
    def encoded_string(query):
        return urlencode(query, True).replace("%40", "@")

    @staticmethod
    def clean_none_value(d) -> dict:
        out = {}
        for k in d.keys():
            if d[k] is not None:
                out[k] = d[k]
        return out

    def _prepare_params(self, params):
        return self.encoded_string(self.clean_none_value(params))

    # TODO ed25519_signature
    def _get_sign(self, payload):
        m = hmac.new(self.secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256)
        return m.hexdigest()

    def _sign_request(self, http_method, url_path, payload=None):
        if payload is None:
            payload = {}
        payload["timestamp"] = self._get_timestamp()
        query_string = self._prepare_params(payload)
        payload["signature"] = self._get_sign(query_string)
        return self._send_request(http_method, url_path, payload)

    def _dispatch_request(self, http_method):
        return {
            "GET": self.session.get,
            "DELETE": self.session.delete,
            "PUT": self.session.put,
            "POST": self.session.post,
        }.get(http_method, "GET")

    def _send_request(self, method: str, urn: str, data: dict) -> Tuple[dict, bool]:
        url = self.uri + urn

        params = self.clean_none_value(
            {
                "url": url,
                "params": self._prepare_params(data),
                "timeout": self.timeout,
            }
        )

        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json;charset=utf-8',
        }
        self.session.headers.update(headers)
        response = self._dispatch_request(method)(**params)

        if response.ok:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text

            return payload, True

        return {
            'status_code': response.status_code,
            'reason': response.reason
        }, False

    def get_status(self):
        urn = '/sapi/v1/system/status'
        method = 'GET'
        data = {}

        res, is_ok = self._request(data, urn, method)
        return (res, True) if res['status'] == 0 else (res, False)

    def get_coins(self):
        urn = '/sapi/v1/capital/config/getall'
        method = 'GET'
        payload = {}

        return self._sign_request(method, urn, payload)

    def get_symbols(self):
        urn = '/sapi/v1/margin/allPairs'
        method = 'GET'
        data = {}

        return self._request(data, urn, method)
