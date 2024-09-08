from django.test import TestCase, SimpleTestCase

from market_data.models import ExchangeInfo, Interval, Kline
from base.test_helper import TestHelperMixin
from indicators.models import MovingAverage
from datetime import datetime, timedelta


class IndicatorsTestCase(TestCase, TestHelperMixin):
    def setUp(self):
        self.exchange_info = self.create_exchange_info()
        self.interval_1m = self.create_interval()
        # self.interval_1h = self.create_interval('HOUR_1')
        # self.create_kline = self.create_kline(symbol=self.exchange_info)

    def test_moving_average_sma(self):
        open_time = datetime.now().replace(second=0, microsecond=0)
        kline_data = [
            {  # 15
                'high_price': 20.0,
                'low_price': 10.0,
                'open_time': open_time,
            },
            {  # 30
                'high_price': 40.0,
                'low_price': 20.0,
                'open_time': open_time - timedelta(minutes=1),
            },
            {  # 30
                'high_price': 50.0,
                'low_price': 10.0,
                'open_time': open_time - timedelta(minutes=2),
            },
        ]
        for item in kline_data:
            self.create_kline(
                symbol=self.exchange_info,
                open_time=item['open_time'],
                high_price=item['high_price'],
                low_price=item['low_price'],
            )

        kline_older = Kline.objects.all().order_by('-open_time').first()

        moving_average = MovingAverage.objects.create(
            name='some_name',
            type=MovingAverage.Type.SMA,
            kline_count=3,
            symbol=self.exchange_info,
            interval=self.interval_1m,
        )

        result = moving_average.get_value(kline=kline_older)
        self.assertEqual(result, 25)
