from core.utils.db_utils import BaseModel
from django.contrib.postgres.fields import ArrayField, HStoreField
from django.db import models


class ExchangeInfo(BaseModel):
    rate_limits = ArrayField(
        HStoreField(),
        null=True, blank=True,
        verbose_name='rate_limits',
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
        return
