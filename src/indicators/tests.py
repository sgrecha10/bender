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
            count=100,
        )
        self.moving_average = MovingAverage.objects.create(
            codename='some_name',
            data_source=MovingAverage.DataSource.HIGH_LOW,
            type=MovingAverage.Type.SMA,
            kline_count=3,
            symbol=self.exchange_info,
            interval=AllowedInterval.MINUTE_1,
        )
        qs = Kline.objects.all().group_by_interval(interval=AllowedInterval.MINUTE_1)
        self.df = qs.to_dataframe(index='open_time_group')

    def test_get_source_df(self):
        df = self.moving_average.get_source_df()
        self.assertEqual(len(df), 100)

        self.moving_average.interval = AllowedInterval.HOUR_1
        self.moving_average.save(update_fields=['interval'])

        df = self.moving_average.get_source_df()
        self.assertEqual(len(df), 2)

    def test_open_time_wrong(self):
        open_time = timezone.now()
        value = self.moving_average.get_value_by_index(
            index=open_time,
            source_df=self.df,
        )
        self.assertEqual(value, None)

    def test_sma(self):
        open_time = self.klines_list[5].open_time
        value = self.moving_average.get_value_by_index(
            index=open_time,
            source_df=self.df,
        )
        self.assertEqual(value, 25)

    def test_sma_1(self):
        self.klines_list[4].high_price = 70.0
        self.klines_list[4].save(update_fields=['high_price'])
        self.klines_list[3].low_price = 5.0
        self.klines_list[3].save(update_fields=['low_price'])

        qs = Kline.objects.all().group_by_interval(interval=AllowedInterval.MINUTE_1)
        df = qs.to_dataframe(index='open_time_group')

        open_time = self.klines_list[5].open_time

        value = self.moving_average.get_value_by_index(
            index=open_time,
            source_df=df,
        )
        self.assertEqual(value, Decimal('29.16666666666666666666666667'))

    def test_sma_2(self):
        open_time = self.klines_list[5].open_time
        self.moving_average.kline_count = 100
        self.moving_average.save(update_fields=['kline_count'])
        value = self.moving_average.get_value_by_index(
            index=open_time,
            source_df=self.df,
        )
        self.assertEqual(value, None)


class MovingAverageNewTest(TestCase, TestHelperMixin):
    def setUp(self):
        self.exchange_info = self.create_exchange_info()
        self.klines_list = self.create_klines(
            symbol=self.exchange_info,
            count=1000,
        )

        open_price = 5
        for i, kline in enumerate(self.klines_list):
            kline.open_price = open_price
            kline.high_price = open_price * i + 10
            kline.low_price = open_price * i - 10
            kline.close_price = open_price + 10
            kline.save()
            open_price = kline.close_price

        self.moving_average = MovingAverage.objects.create(
            codename='some_name',
            data_source=MovingAverage.DataSource.HIGH_LOW,
            type=MovingAverage.Type.SMA,
            kline_count=10,
            symbol=self.exchange_info,
            interval=AllowedInterval.MINUTE_1,
        )

    def test_get_source_df_base(self):
        source_df = self.moving_average.get_source_df()
        self.assertEqual(len(source_df), 1000)

        kline_qs = Kline.objects.all().group_by_interval()
        kline_df = kline_qs.to_dataframe(index='open_time_group')
        self.assertTrue(kline_df.equals(source_df))

        #  то же самое, но с группировкой
        self.moving_average.interval = AllowedInterval.HOUR_1
        self.moving_average.save(update_fields=['interval'])

        source_df = self.moving_average.get_source_df()
        self.assertEqual(len(source_df), 17)

        kline_qs = Kline.objects.all().group_by_interval(interval=AllowedInterval.HOUR_1)
        kline_df = kline_qs.to_dataframe(index='open_time_group')
        self.assertTrue(kline_df.equals(source_df))

    def test_get_value_by_index_1m(self):
        index_1 = self.klines_list[20].open_time
        index_2 = self.klines_list[30].open_time
        index_3 = self.klines_list[40].open_time

        get_value_by_index_result_1_1 = self.moving_average.get_value_by_index(index=index_1)
        get_value_by_index_result_1_2 = self.moving_average.get_value_by_index(index=index_2)
        get_value_by_index_result_1_3 = self.moving_average.get_value_by_index(index=index_3)

        source_df = self.moving_average.get_source_df()
        get_value_by_index_result_2_1 = self.moving_average.get_value_by_index(
            index=index_1,
            source_df=source_df,
        )
        get_value_by_index_result_2_2 = self.moving_average.get_value_by_index(
            index=index_2,
            source_df=source_df,
        )
        get_value_by_index_result_2_3 = self.moving_average.get_value_by_index(
            index=index_3,
            source_df=source_df,
        )

        self.assertEqual(get_value_by_index_result_1_1, get_value_by_index_result_2_1)
        self.assertEqual(get_value_by_index_result_1_2, get_value_by_index_result_2_2)
        self.assertEqual(get_value_by_index_result_1_3, get_value_by_index_result_2_3)

        base_df = source_df[20:40]
        self.assertEqual(len(base_df), 20)

        source_df = self.moving_average.get_source_df(base_df=base_df)
        get_value_by_index_result_3_1 = self.moving_average.get_value_by_index(
            index=index_1,
            source_df=source_df,
        )
        get_value_by_index_result_3_2 = self.moving_average.get_value_by_index(
            index=index_2,
            source_df=source_df,
        )
        get_value_by_index_result_3_3 = self.moving_average.get_value_by_index(
            index=index_3,
            source_df=source_df,
        )

        self.assertEqual(get_value_by_index_result_1_1, get_value_by_index_result_3_1)
        self.assertEqual(get_value_by_index_result_1_2, get_value_by_index_result_3_2)
        self.assertEqual(get_value_by_index_result_1_3, get_value_by_index_result_3_3)

    def test_get_value_by_index_1h(self):
        self.moving_average.interval = AllowedInterval.HOUR_1
        self.moving_average.kline_count = 3
        self.moving_average.save(update_fields=['interval', 'kline_count'])

        kline_qs = Kline.objects.all().group_by_interval(interval=AllowedInterval.HOUR_1)
        kline_df = kline_qs.to_dataframe(index='open_time_group')
        source_df = self.moving_average.get_source_df()
        self.assertTrue(kline_df.equals(source_df))

        base_df = source_df[5:10]
        self.assertEqual(len(base_df), 5)

        index_1 = base_df.iloc[0].name
        index_2 = base_df.iloc[2].name
        index_3 = base_df.iloc[-1].name

        get_value_by_index_result_1_1 = self.moving_average.get_value_by_index(index=index_1)
        get_value_by_index_result_1_2 = self.moving_average.get_value_by_index(index=index_2)
        get_value_by_index_result_1_3 = self.moving_average.get_value_by_index(index=index_3)

        self.assertEqual(len(source_df), 17)
        get_value_by_index_result_2_1 = self.moving_average.get_value_by_index(
            index=index_1,
            source_df=source_df,
        )
        get_value_by_index_result_2_2 = self.moving_average.get_value_by_index(
            index=index_2,
            source_df=source_df,
        )
        get_value_by_index_result_2_3 = self.moving_average.get_value_by_index(
            index=index_3,
            source_df=source_df,
        )

        self.assertEqual(get_value_by_index_result_1_1, get_value_by_index_result_2_1)
        self.assertEqual(get_value_by_index_result_1_2, get_value_by_index_result_2_2)
        self.assertEqual(get_value_by_index_result_1_3, get_value_by_index_result_2_3)

        source_df = self.moving_average.get_source_df(base_df=base_df)
        self.assertEqual(len(source_df), 9)
        get_value_by_index_result_3_1 = self.moving_average.get_value_by_index(
            index=index_1,
            source_df=source_df,
        )
        get_value_by_index_result_3_2 = self.moving_average.get_value_by_index(
            index=index_2,
            source_df=source_df,
        )
        get_value_by_index_result_3_3 = self.moving_average.get_value_by_index(
            index=index_3,
            source_df=source_df,
        )

        self.assertEqual(get_value_by_index_result_1_1, get_value_by_index_result_3_1)
        self.assertEqual(get_value_by_index_result_1_2, get_value_by_index_result_3_2)
        self.assertEqual(get_value_by_index_result_1_3, get_value_by_index_result_3_3)
