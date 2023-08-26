from django.conf import settings
from django.db import models

from core.clients.binance.restapi import BinanceClient
from core.utils.db_utils import BaseModel
import requests


class SpotBalance(BaseModel):
    coin = models.CharField(
        verbose_name='coin',
        max_length=50,
        unique=True,
    )
    deposit_all_enable = models.BooleanField(
        verbose_name='depositAllEnable',
    )
    free = models.DecimalField(
        verbose_name='free',
        max_digits=12,
        decimal_places=10,
    )
    freeze = models.DecimalField(
        verbose_name='freeze',
        max_digits=12,
        decimal_places=10,
    )
    ipoable = models.DecimalField(
        verbose_name='ipoable',
        max_digits=12,
        decimal_places=10,
    )
    ipoing = models.DecimalField(
        verbose_name='ipoing',
        max_digits=12,
        decimal_places=10,
    )
    is_legal_money = models.BooleanField(
        verbose_name='isLegalMoney',
    )
    locked = models.DecimalField(
        verbose_name='locked',
        max_digits=12,
        decimal_places=10,
    )
    name = models.CharField(
        verbose_name='name',
        max_length=50,
    )
    storage = models.DecimalField(
        verbose_name='storage',
        max_digits=12,
        decimal_places=10,
    )
    trading = models.BooleanField(
        verbose_name='trading',
    )
    withdraw_all_enable = models.BooleanField(
        verbose_name='withdrawAllEnable',
    )
    withdrawing = models.DecimalField(
        verbose_name='withdrawing',
        max_digits=12,
        decimal_places=10,
    )

    class Meta:
        verbose_name = 'SPOT баланс'
        verbose_name_plural = 'SPOT баланс'

    def __str__(self):
        return self.coin

    @classmethod
    def get_update(cls):
        client = BinanceClient(settings.BINANCE_CLIENT)
        try:
            result, is_ok = client.get_capital_config_getall()  # noqa
        except requests.ConnectionError as e:
            return e, False

        i = 0
        if is_ok:
            for item in result:
                cls.objects.update_or_create(
                    coin=item['coin'],
                    defaults={
                        'deposit_all_enable': item['depositAllEnable'],
                        'free': item['free'],
                        'freeze': item['freeze'],
                        'ipoable': item['ipoable'],
                        'ipoing': item['ipoing'],
                        'is_legal_money': item['isLegalMoney'],
                        'locked': item['locked'],
                        'name': item['name'],
                        'storage': item['storage'],
                        'trading': item['trading'],
                        'withdraw_all_enable': item['withdrawAllEnable'],
                        'withdrawing': item['withdrawing'],
                    },
                )
                i += 1

        return i if is_ok else result, is_ok


class TradeFee(BaseModel):
    symbol = models.CharField(
        verbose_name='symbol',
        max_length=50,
        unique=True,
    )
    maker_commission = models.DecimalField(
        verbose_name='maker_commission',
        max_digits=5,
        decimal_places=4,
    )
    taker_commission = models.DecimalField(
        verbose_name='taker_commission',
        max_digits=5,
        decimal_places=4,
    )

    class Meta:
        verbose_name = 'Торговая комиссия'
        verbose_name_plural = 'Торговые комиссии'

    def __str__(self):
        return self.symbol

    @classmethod
    def get_update(cls, symbol=None):
        client = BinanceClient(settings.BINANCE_CLIENT)
        try:
            result, is_ok = client.get_trade_fee(symbol)  # noqa
        except requests.ConnectionError as e:
            return e, False

        i = 0
        if is_ok:
            for item in result:
                cls.objects.update_or_create(
                    symbol=item['symbol'],
                    defaults={
                        'maker_commission': item['makerCommission'],
                        'taker_commission': item['takerCommission'],
                    },
                )
                i += 1

        return i if is_ok else result, is_ok
