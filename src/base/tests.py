from django.test import TestCase

from base.helpers import TestHelperMixin
from market_data.models import Kline, ExchangeInfo


class TestHelperMixinTest(TestCase):
    def setUp(self):
        self.mixin = TestHelperMixin()

    def test_create_exchange_info(self):
        result = self.mixin.create_exchange_info()
        self.assertTrue(isinstance(result, ExchangeInfo))

        result = self.mixin.create_exchange_info(symbol='SOME_SYMBOL')
        self.assertEqual(result.symbol, 'SOME_SYMBOL')

    def test_create_klines(self):
        exchange_info = self.mixin.create_exchange_info()
        result = self.mixin.create_klines(symbol=exchange_info.symbol)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].symbol_id, exchange_info.symbol)
        Kline.objects.all().delete()

        result = self.mixin.create_klines(symbol=exchange_info)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].symbol_id, exchange_info.symbol)
        Kline.objects.all().delete()

        result = self.mixin.create_klines(
            symbol=exchange_info,
            count=100,
        )
        self.assertEqual(len(result), 100)
        self.assertEqual(result[0].symbol_id, exchange_info.symbol)
