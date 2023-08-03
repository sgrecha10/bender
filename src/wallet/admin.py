from django.conf import settings
from django.contrib import admin, messages
from django.http.response import HttpResponseRedirect
from django.urls import path, reverse

from core.clients.binance import BinanceClient

from .models import Coin


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
        client = BinanceClient(settings.BINANCE_CLIENT)
        result, is_ok = client.get_coins()

        if not is_ok:
            messages.error(request, 'Нет соединения с Binance')
            meta = self.model._meta
            url = reverse(
                f'admin:{meta.app_label}_{meta.model_name}_changelist'
            )
            return HttpResponseRedirect(url)

        for item in result:
            Coin.objects.update_or_create(
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

        messages.success(request, 'Запущено обновление торговых пар')
        meta = self.model._meta
        url = reverse(f'admin:{meta.app_label}_{meta.model_name}_changelist')
        return HttpResponseRedirect(url)
