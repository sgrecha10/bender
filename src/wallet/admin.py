from django.contrib import admin, messages
from django.http.response import HttpResponseRedirect
from django.urls import path, reverse

from wallet.tasks import task_get_capital_config_getall, task_update_trade_fee

from .models import SpotBalance, TradeFee


@admin.register(SpotBalance)
class CoinAdmin(admin.ModelAdmin):
    change_list_template = "admin/wallet/coin/change_list.html"
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
                'update_all/',
                self.set_capital_config_getall,
                name='update_all',
            ),
        ]
        return added_urls + urls

    def set_capital_config_getall(self, request, *_):
        # client = Spot(
        #     api_key=settings.BINANCE_CLIENT['api_key'],
        #     api_secret=settings.BINANCE_CLIENT['secret_key'],
        # )
        # pprint(client.account())
        # return

        task_get_capital_config_getall.delay()
        messages.success(request, 'Update started..')
        meta = self.model._meta
        url = reverse(f'admin:{meta.app_label}_{meta.model_name}_changelist')
        return HttpResponseRedirect(url)


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

    def update_trade_fee(self, request, *_):
        task_update_trade_fee.delay()

        messages.success(request, 'Update started..')
        meta = self.model._meta
        url = reverse(f'admin:{meta.app_label}_{meta.model_name}_changelist')
        return HttpResponseRedirect(url)

    @admin.display(description='maker_commission', ordering='maker_commission')
    def get_maker_commission(self, obj):
        return f'{obj.maker_commission:.2%}'

    @admin.display(description='taker_commission', ordering='taker_commission')
    def get_taker_commission(self, obj):
        return f'{obj.taker_commission:.2%}'
