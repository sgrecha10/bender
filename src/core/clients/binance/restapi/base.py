import hashlib
import hmac
from typing import Tuple
from urllib.parse import urlencode

import requests
from django.conf import settings

from core.utils.client_utils import get_timestamp
from core.utils.value_utils import clean_none_value


class BinanceBaseRestClient:
    timeout = 10

    def __init__(self):
        self.session = requests.Session()
        self.uri = settings.BINANCE_CLIENT['uri']
        self.api_key = settings.BINANCE_CLIENT['api_key']
        self.secret_key = settings.BINANCE_CLIENT['secret_key']

    @staticmethod
    def encoded_string(query):
        return urlencode(query, True).replace("%40", "@")

    def _prepare_params(self, params):
        return self.encoded_string(clean_none_value(params))

    # TODO ed25519_signature
    def _get_sign(self, payload):
        m = hmac.new(
            self.secret_key.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        )
        return m.hexdigest()

    def _dispatch_request(self, http_method):
        return {
            "GET": self.session.get,
            "DELETE": self.session.delete,
            "PUT": self.session.put,
            "POST": self.session.post,
        }.get(http_method, "GET")

    def sign_request(self, http_method, url_path, payload=None):
        if payload is None:
            payload = {}

        payload["timestamp"] = get_timestamp()
        query_string = self._prepare_params(payload)
        payload["signature"] = self._get_sign(query_string)
        return self.send_request(http_method, url_path, payload)

    def send_request(
        self, http_method, url_path, payload=None
    ) -> Tuple[dict, bool]:
        if payload is None:
            payload = {}

        url = self.uri + url_path
        params = clean_none_value(
            {
                "url": url,
                "params": self._prepare_params(payload),
                "timeout": self.timeout,
            }
        )
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json;charset=utf-8',
        }
        self.session.headers.update(
            headers
        )  # TO DO настроить количество повторов в requests
        response = self._dispatch_request(http_method)(**params)

        if response.ok:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text

            return payload, True

        return {
            'status_code': response.status_code,
            'reason': response.reason,
        }, False
