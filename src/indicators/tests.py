from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from base.helpers import TestHelperMixin
from indicators.models import MovingAverage
from market_data.constants import AllowedInterval
from market_data.models import Kline


class MovingAverageTest(TestCase, TestHelperMixin):
    def setUp(self):
        self.exchange_info = self.create_exchange_info()
        self.klines_list = self.create_klines(
            symbol=self.exchange_info,
            count=10,
        )
        self.moving_average = MovingAverage.objects.create(
            name='some_name',
            data_source=MovingAverage.DataSource.HIGH_LOW,
            type=MovingAverage.Type.SMA,
            kline_count=3,
            # symbol=self.exchange_info,
            # interval=AllowedInterval.MINUTE_1,
        )
        qs = Kline.objects.all().group_by_interval(interval=AllowedInterval.MINUTE_1)
        self.df = qs.to_dataframe(index='open_time_group')

    def test_open_time_wrong(self):
        open_time = timezone.now()
        value = self.moving_average.get_value_by_index(
            index=open_time,
            df=self.df,
        )
        self.assertEqual(value, None)

    def test_sma(self):
        open_time = self.klines_list[-5].open_time
        value = self.moving_average.get_value_by_index(
            index=open_time,
            df=self.df,
        )
        self.assertEqual(value, 25)

    def test_sma_1(self):
        self.klines_list[4].high_price = 70.0
        self.klines_list[4].save(update_fields=['high_price'])
        self.klines_list[3].low_price = 5.0
        self.klines_list[3].save(update_fields=['low_price'])

        qs = Kline.objects.all().group_by_interval(interval=AllowedInterval.MINUTE_1)
        df = qs.to_dataframe(index='open_time_group')

        open_time = self.klines_list[-5].open_time
        value = self.moving_average.get_value_by_index(
            index=open_time,
            df=df,
        )
        self.assertEqual(value, Decimal('29.16666666666666666666666667'))

    def test_sma_2(self):
        open_time = self.klines_list[-5].open_time
        self.moving_average.kline_count = 100
        self.moving_average.save(update_fields=['kline_count'])
        value = self.moving_average.get_value_by_index(
            index=open_time,
            df=self.df,
        )
        self.assertEqual(value, None)
