from django.contrib import admin, messages
from django.http.response import HttpResponseRedirect
from django.urls import path, reverse

from wallet.tasks import (
    task_get_coins,
    task_update_trade_fee,
)
from .models import Coin, TradeFee


@admin.register(Coin)
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
                'update_coins/',
                self.set_update_coins,
                name='update_coins',
            ),
        ]
        return added_urls + urls

    def set_update_coins(self, request, *_):
        # client = Spot(api_key=settings.BINANCE_CLIENT['api_key'], api_secret=settings.BINANCE_CLIENT['secret_key'])
        # pprint(client.account())
        # return

        task_get_coins.delay()
        messages.success(request, 'Запущено обновление торговых пар')
        meta = self.model._meta
        url = reverse(f'admin:{meta.app_label}_{meta.model_name}_changelist')
        return HttpResponseRedirect(url)


@admin.register(TradeFee)
class TradeFeeAdmin(admin.ModelAdmin):
    change_list_template = "admin/wallet/trade_fee/change_list.html"
    list_display = ('symbol', 'maker_commission', 'taker_commission', 'updated')
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
