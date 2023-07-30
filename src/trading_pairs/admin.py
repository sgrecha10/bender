from django.contrib import admin

from .models import TradingPair


@admin.register(TradingPair)
class TradingPairAdmin(admin.ModelAdmin):
    change_list_template = "admin/trading_pairs/trading_pair/change_list.html"
    list_display = (
        'symbol', 'binance_id', 'base', 'quote', 'is_margin_trade',
        'is_buy_allowed', 'is_sell_allowed', 'updated', 'created',
    )
    readonly_fields = ('id',) + list_display

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
