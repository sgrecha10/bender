from django.contrib import admin
from django.urls import path

from core.utils.admin_utils import redirect_to_change_list
from .models import SpotBalance, TradeFee


@admin.register(SpotBalance)
class SpotBalanceAdmin(admin.ModelAdmin):
    change_list_template = "admin/wallet/spot_balance/change_list.html"
    list_display = (
        'coin',
        'name',
        'deposit_all_enable',
        'free',
        'freeze',
        'ipoable',
        'ipoing',
        'is_legal_money',
        'locked',
        'storage',
        'trading',
        'withdraw_all_enable',
        'withdrawing',
        'updated',
    )
    readonly_fields = list_display
    search_fields = ('coin', 'name')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path(
                'update_capital_config_getall/',
                self.update_capital_config_getall,
                name='update_capital_config_getall',
            ),
        ]
        return added_urls + urls

    def update_capital_config_getall(self, request):
        result, is_ok = self.model.get_update()
        message = f'Обновили {result} записей' if is_ok else result
        return redirect_to_change_list(request, self.model, message, is_ok)

        # client = Spot(
        #     api_key=settings.BINANCE_CLIENT['api_key'],
        #     api_secret=settings.BINANCE_CLIENT['secret_key'],
        # )
        # pprint(client.account())
        # return


@admin.register(TradeFee)
class TradeFeeAdmin(admin.ModelAdmin):
    change_list_template = "admin/wallet/trade_fee/change_list.html"
    list_display = (
        'symbol',
        'get_maker_commission',
        'get_taker_commission',
        'updated',
    )
    readonly_fields = list_display
    search_fields = ('symbol',)
    list_filter = ('symbol', 'maker_commission', 'taker_commission')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='maker_commission', ordering='maker_commission')
    def get_maker_commission(self, obj):
        return f'{obj.maker_commission:.2%}'

    @admin.display(description='taker_commission', ordering='taker_commission')
    def get_taker_commission(self, obj):
        return f'{obj.taker_commission:.2%}'

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path(
                'update_trade_fee/',
                self.update_trade_fee,
                name='update_trade_fee',
            ),
        ]
        return added_urls + urls

    def update_trade_fee(self, request, symbol=None):
        result, is_ok = self.model.get_update(symbol)
        message = f'Обновили {result} записей' if is_ok else result
        return redirect_to_change_list(request, self.model, message, is_ok)
