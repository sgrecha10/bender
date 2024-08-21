import requests
from django.conf import settings
from django.contrib.postgres.fields import ArrayField, HStoreField
from django.db import models

from core.clients.binance.restapi import BinanceClient
from core.utils.db_utils import BaseModel


class ExchangeInfo(BaseModel):
    rate_limits = ArrayField(
        HStoreField(),
        null=True, blank=True,
        verbose_name='rateLimits',
    )
    # exchange_filters = ArrayField(
    #     models.CharField(max_length=255),
    #     null=True, blank=True,
    #     verbose_name='exchange_filters',
    # )

    symbol = models.CharField(
        verbose_name='symbol',
        max_length=20,
    )
    status = models.CharField(
        verbose_name='status',
        max_length=20,
        null=True, blank=True,
        default=None,
    )
    base_asset = models.CharField(
        verbose_name='baseAsset',
        max_length=20,
        null=True, blank=True,
        default=None,
    )
    base_asset_precision = models.PositiveSmallIntegerField(
        verbose_name='baseAssetPrecision',
        null=True, blank=True,
    )
    quoteAsset = models.CharField(
        verbose_name='quoteAsset',
        max_length=20,
        null=True, blank=True,
        default=None,
    )
    quote_precision = models.PositiveSmallIntegerField(
        verbose_name='quotePrecision',
        null=True, blank=True,
    )
    quote_asset_precision = models.PositiveSmallIntegerField(
        verbose_name='quoteAssetPrecision',
        null=True, blank=True,
    )
    base_commission_precision = models.PositiveSmallIntegerField(
        verbose_name='baseCommissionPrecision',
        null=True, blank=True,
    )
    quote_commission_precision = models.PositiveSmallIntegerField(
        verbose_name='quoteCommissionPrecision',
        null=True, blank=True,
    )
    order_types = ArrayField(
        models.CharField(max_length=20),
        null=True, blank=True,
        verbose_name='orderTypes',
    )
    iceberg_allowed = models.BooleanField(
        verbose_name='icebergAllowed',
        default=False,
    )
    oco_allowed = models.BooleanField(
        verbose_name='ocoAllowed',
        default=False,
    )
    quote_order_qty_market_allowed = models.BooleanField(
        verbose_name='quoteOrderQtyMarketAllowed',
        default=False,
    )
    allow_trailing_stop = models.BooleanField(
        verbose_name='allowTrailingStop',
        default=False,
    )
    cancel_replace_allowed = models.BooleanField(
        verbose_name='cancelReplaceAllowed',
        default=False,
    )
    is_spot_trading_allowed = models.BooleanField(
        verbose_name='isSpotTradingAllowed',
        default=False,
    )
    is_margin_trading_allowed = models.BooleanField(
        verbose_name='isMarginTradingAllowed',
        default=False,
    )
    # filters = ArrayField(
    #     models.CharField(max_length=20),
    #     null=True, blank=True,
    #     verbose_name='filters',
    # )

    permissions = ArrayField(
        models.CharField(max_length=20),
        null=True, blank=True,
        verbose_name='permissions',
    )
    default_self_trade_prevention_mode = models.CharField(
        verbose_name='defaultSelfTradePreventionMode',
        max_length=20,
        null=True, blank=True,
        default=None,
    )
    allowed_self_trade_prevention_modes = ArrayField(
        models.CharField(max_length=20),
        null=True, blank=True,
        verbose_name='allowedSelfTradePreventionModes',
    )


    class Meta:
        verbose_name = 'Exchange Information'
        verbose_name_plural = 'Exchange Information'

    def __str__(self):
        return self.symbol

    @classmethod
    def get_update(cls, symbol=None, symbols=None, permissions=None):
        client = BinanceClient(settings.BINANCE_CLIENT)
        try:
            result, is_ok = client.get_exchange_info(symbol, symbols, permissions)  # noqa
        except requests.ConnectionError as e:
            return e, False

        i = 0
        if is_ok:
            for item in result['symbols']:
                cls.objects.update_or_create(
                    symbol=item['symbol'],
                    defaults={
                        'server_time': result['serverTime'],
                        'rate_limits': result['rateLimits'],
                        # 'exchange_filters': item['exchange_filters'],
                        'symbol': item['symbol'],
                        'status': item['status'],
                        'base_asset': item['baseAsset'],
                        'base_asset_precision': item['baseAssetPrecision'],
                        'quoteAsset': item['quoteAsset'],
                        'quote_precision': item['quotePrecision'],
                        'quote_asset_precision': item['quoteAssetPrecision'],
                        'base_commission_precision': item['baseCommissionPrecision'],
                        'quote_commission_precision': item['quoteCommissionPrecision'],
                        'order_types': item['orderTypes'],
                        'iceberg_allowed': item['icebergAllowed'],
                        'oco_allowed': item['ocoAllowed'],
                        'quote_order_qty_market_allowed': item['quoteOrderQtyMarketAllowed'],
                        'allow_trailing_stop': item['allowTrailingStop'],
                        'cancel_replace_allowed': item['cancelReplaceAllowed'],
                        'is_spot_trading_allowed': item['isSpotTradingAllowed'],
                        'is_margin_trading_allowed': item['isMarginTradingAllowed'],
                        # 'filters': item['filters'],
                        'permissions': item['permissions'],
                        'default_self_trade_prevention_mode': item['defaultSelfTradePreventionMode'],
                        'allowed_self_trade_prevention_modes': item['allowedSelfTradePreventionModes'],
                    },
                )
                i += 1

        return i if is_ok else result, is_ok


class Interval(models.Model):
    codename = models.CharField(
        verbose_name='codename',
        max_length=15,
        primary_key=True,
    )
    value = models.CharField(
        verbose_name='value',
        max_length=4,
    )

    class Meta:
        verbose_name = 'Interval'
        verbose_name_plural = 'Interval'

    def __str__(self):
        return self.codename


class Kline(BaseModel):
    symbol = models.ForeignKey(
        ExchangeInfo, on_delete=models.CASCADE,
        verbose_name='symbol',
        related_name='klines',
    )
    open_time = models.DateTimeField(
        verbose_name='openTime',
    )
    open_price = models.DecimalField(
        verbose_name='openPrice',
        max_digits=20,
        decimal_places=10,
    )
    high_price = models.DecimalField(
        verbose_name='highPrice',
        max_digits=20,
        decimal_places=10,
    )
    low_price = models.DecimalField(
        verbose_name='lowPrice',
        max_digits=20,
        decimal_places=10,
    )
    close_price = models.DecimalField(
        verbose_name='closePrice',
        max_digits=20,
        decimal_places=10,
    )
    volume = models.DecimalField(
        verbose_name='volume',
        max_digits=20,
        decimal_places=10,
    )
    close_time = models.DateTimeField(
        verbose_name='closeTime',
    )
    quote_asset_volume = models.DecimalField(
        verbose_name='quoteAssetVolume',
        max_digits=20,
        decimal_places=10,
    )
    number_of_trades = models.PositiveIntegerField(
        verbose_name='numberOfTrades',
    )
    taker_buy_base_asset_volume = models.DecimalField(
        verbose_name='takerBuyBaseAssetVolume',
        max_digits=20,
        decimal_places=10,
    )
    taker_buy_quote_asset_volume = models.DecimalField(
        verbose_name='takerBuyQuoteAssetVolume',
        max_digits=20,
        decimal_places=10,
    )
    unused_field_ignore =models.BooleanField(
        verbose_name='unusedFieldIgnore',
    )

    class Meta:
        verbose_name = 'Kline'
        verbose_name_plural = 'Kline'
