from typing import Union
from unittest import mock

from django.conf import settings
from django.test.testcases import SimpleTestCase

from core.clients.binance.restapi import BinanceClient


# class DummyHTTPResponse:
#     status_code = 200
#
#     def __init__(
#         self, data: Union[list, dict, str, None] = None, **kwargs
#     ) -> None:
#         self.data = data
#         self.text = data
#         for key, val in kwargs.items():
#             setattr(self, key, val)
#
#     def json(self):
#         if isinstance(self.data, (dict, list)):
#             return self.data
#         raise ValueError
#
#     @property
#     def ok(self):
#         return self.status_code < 400
#
#
# class BinanceClientTest(SimpleTestCase):
#     def setUp(self):
#         self.client = BinanceClient(settings.BINANCE_CLIENT)
#
#     @mock.patch('requests.sessions.Session.send')
#     def test_get_status(self, mock_send):
#         resp_data = {'msg': 'normal', 'status': 0}
#         mock_send.return_value = DummyHTTPResponse(resp_data)
#         res, is_ok = self.client.get_status()
#         self.assertTrue(is_ok)
#         self.assertEqual(res, resp_data)
#
#     def test_get_symbols(self):
#         res, is_ok = self.client.get_symbols()
#         self.assertTrue(is_ok)
#         self.assertEqual(res, {})
