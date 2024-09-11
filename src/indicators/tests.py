from django.test import TestCase, SimpleTestCase

from market_data.models import ExchangeInfo, Kline
from base.helpers import TestHelperMixin
# from indicators.models import MovingAverage
from datetime import datetime, timedelta
import market_data.constants as const


# class IndicatorsTestCase(TestCase, TestHelperMixin):
#     def setUp(self):
#         self.exchange_info = self.create_exchange_info()
#         # self.interval_1m = self.create_interval()
#         # self.interval_1h = self.create_interval(const.HOUR_1)
#
#     def test_moving_average_sma(self):
#         klines_list = self.create_klines(
#             symbol=self.exchange_info,
#             count=10,
#         )
#
#         # moving_average = MovingAverage.objects.create(
#         #     name='some_name',
#         #     type=MovingAverage.Type.SMA,
#         #     kline_count=3,
#         #     symbol=self.exchange_info,
#         #     interval=self.interval_1m,
#         # )
#     #
#     #     result = moving_average.get_value(kline=kline_older)
#     #     self.assertEqual(result, 25)
