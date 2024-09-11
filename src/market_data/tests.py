from decimal import Decimal

from django.test import TestCase

from base.helpers import TestHelperMixin
from .constants import Interval
from .models import Kline


class TestManagerKline(TestCase, TestHelperMixin):
    def setUp(self):
        self.exchange_info = self.create_exchange_info()
        kline_list = self.create_klines(
            symbol=self.exchange_info,
            count=1000,
        )
        kline_list[0].open_price = 15.0
        kline_list[0].save(update_fields=['open_price'])

        kline_list[1].high_price = 137.0
        kline_list[1].save(update_fields=['high_price'])

    def test_group_by_interval(self):
        qs = Kline.objects.all()

        qs_minute_1 = qs.group_by_interval(interval=Interval.MINUTE_1)
        self.assertEqual(qs_minute_1.count(), 1000)

        qs_hour_1 = qs.group_by_interval(interval=Interval.HOUR_1).order_by('open_time_group')
        self.assertEqual(qs_hour_1.count(), 17)
        self.assertEqual(qs_hour_1[0]['open_price'], Decimal(15))
        self.assertEqual(qs_hour_1[0]['high_price'], Decimal(137))
        self.assertEqual(qs_hour_1[0]['volume'], Decimal(60000))
        self.assertEqual(qs_hour_1[16]['volume'], Decimal(40000))

        qs_day_1 = qs.group_by_interval(interval=Interval.DAY_1)
        self.assertEqual(qs_day_1.count(), 1)
        self.assertEqual(qs_day_1[0]['volume'], Decimal(1000000))
