from django.test import TestCase
from base.helpers import TestHelperMixin
from market_data.models import Kline
from arbitrations.models import Arbitration


class ArbitrationsTestCase(TestCase, TestHelperMixin):
    def setUp(self):
        self.exchange_info_1 = self.create_exchange_info()
        self.exchange_info_2 = self.create_exchange_info()

        kline_list_1 = self.create_klines(
            symbol=self.exchange_info_1,
            count=10,
        )
        kline_list_2 = self.create_klines(
            symbol=self.exchange_info_2,
            count=10,
        )

        kline_list_1[0].close_price = 30.0
        kline_list_1[1].close_price = 50.0
        kline_list_1[2].close_price = 40.0
        kline_list_1[3].close_price = 20.0
        kline_list_1[4].close_price = 15.0
        kline_list_1[5].close_price = 25.0
        kline_list_1[6].close_price = 35.0
        kline_list_1[7].close_price = 50.0
        kline_list_1[8].close_price = 40.0
        kline_list_1[9].close_price = 42.0
        Kline.objects.bulk_update(kline_list_1, ['close_price'])

        kline_list_2[0].close_price = 350.0
        kline_list_2[1].close_price = 550.0
        kline_list_2[2].close_price = 450.0
        kline_list_2[3].close_price = 250.0
        kline_list_2[4].close_price = 200.0
        kline_list_2[5].close_price = 300.0
        kline_list_2[6].close_price = 350.0
        kline_list_2[7].close_price = 500.0
        kline_list_2[8].close_price = 450.0
        kline_list_2[9].close_price = 420.0
        Kline.objects.bulk_update(kline_list_2, ['close_price'])

        self.arbitration = Arbitration.objects.create(
            codename='some_name',
            symbol_1=self.exchange_info_1,
            symbol_2=self.exchange_info_2,
            ratio_type=Arbitration.SymbolsRatioType.B_FACTOR,
        )

    def test_get_df(self):
        df = self.arbitration.get_df()
        print(df)
