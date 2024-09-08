from django.test import TestCase
from base.test_helper import TestHelperMixin
from .models import Kline, Interval
import market_data.constants as const


class TestManagerKline(TestCase, TestHelperMixin):
    def setUp(self):
        self.symbol = self.create_exchange_info()
        self.create_klines(
            symbol=self.symbol,
            count=500,
        )

    def test_add_interval_column(self):
        klines_qs = Kline.objects.filter(
            symbol=self.symbol,
        ).add_interval_column(
            interval=const.HOUR_1,
        )
        print(klines_qs)
