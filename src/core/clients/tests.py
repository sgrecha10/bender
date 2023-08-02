from django.test.testcases import SimpleTestCase
from core.clients.binance import BinanceClient
from django.conf import settings
from typing import Union
import json


class DummyHTTPResponse:
    status_code = 200

    def __init__(self, data: Union[list, dict, str, None] = None, **kwargs) -> None:
        self.data = data
        self.text = data
        for key, val in kwargs.items():
            setattr(self, key, val)

    def json(self):
        if isinstance(self.data, (dict, list, str)):
            return self.data
        raise json.JSONDecodeError('', '', 0)

    @property
    def ok(self):
        return self.status_code < 400


class BinanceClientTest(SimpleTestCase):
    def setUp(self):
        self.client = BinanceClient(settings.BINANCE_CLIENT)

    def test_ping(self):
        res, is_ok = self.client.ping()
        self.assertTrue(is_ok)
        self.assertEqual(res, {})

    def test_get_symbols(self):
        res, is_ok = self.client.get_symbols()
        self.assertTrue(is_ok)
        self.assertEqual(res, {})