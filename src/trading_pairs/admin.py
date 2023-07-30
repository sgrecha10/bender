from django.contrib import admin

from .models import TradingPair


@admin.register(TradingPair)
class TradingPairAdmin(admin.ModelAdmin):
    list_display = (
        'symbol', 'binance_id', 'base', 'quote', 'is_margin_trade',
        'is_buy_allowed', 'is_sell_allowed', 'is_favorites', 'updated', 'created',
    )
    readonly_fields = ('id',) + list_display
