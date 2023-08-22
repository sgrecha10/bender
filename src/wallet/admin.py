from django.conf import settings
from django.contrib import admin, messages
from django.http.response import HttpResponseRedirect
from django.urls import path, reverse

from core.clients.binance import BinanceClient

from .models import Coin
from binance.spot import Spot
from pprint import pprint
from wallet.tasks import task_get_coins


@admin.register(Coin)
class CoinAdmin(admin.ModelAdmin):
    change_list_template = "admin/wallet/coin/change_list.html"
    list_display = (
        'id',
        'coin',
        'deposit_all_enable',
        'free',
        'freeze',
        'ipoable',
        'ipoing',
        'is_legal_money',
        'locked',
        'name',
        'storage',
        'trading',
        'withdraw_all_enable',
        'withdrawing',
        'updated',
    )
    readonly_fields = list_display

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

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
