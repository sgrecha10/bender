from django.test import TestCase
from base.helper import TestHelperMixin
from .models import Kline
from .constants import Interval


# class TestManagerKline(TestCase, TestHelperMixin):
#     def setUp(self):
#         self.symbol = self.create_exchange_info()
#         self.create_klines(
#             symbol=self.symbol,
#             count=500,
#         )
#
#     def test_group_by_interval(self):
#         kline = Kline.objects.order_by('open_time').all()[0]
#         kline.open_price = 18
#         kline.save(update_fields=['open_price'])
#
#         kline = Kline.objects.order_by('open_time').all()[1]
#         kline.high_price = 135
#         kline.save(update_fields=['high_price'])
#
#         klines_qs = Kline.objects.filter(
#             symbol=self.symbol,
#         ).group_by_interval(
#             interval=Interval.HOUR_1,
#         )
#         # print(klines_qs)
