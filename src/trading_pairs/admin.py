from django.conf import settings
from django.contrib import admin, messages
from django.http.response import HttpResponseRedirect
from django.urls import path, reverse

from core.clients.binance import BinanceClient

from .models import TradingPair


@admin.register(TradingPair)
class TradingPairAdmin(admin.ModelAdmin):
    change_list_template = "admin/trading_pairs/trading_pair/change_list.html"
    list_display = (
        'id',
        'symbol',
        'binance_id',
        'base',
        'quote',
        'is_margin_trade',
        'is_buy_allowed',
        'is_sell_allowed',
        'updated',
        'created',
    )
    readonly_fields = list_display
    list_display_links = ('symbol',)
    search_fields = ('symbol',)
    list_filter = ('base', 'quote')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path(
                'update_quote/',
                self.set_update_quote,
                name='update_quote',
            ),
        ]
        return added_urls + urls

    def set_update_quote(self, request, *_):
        client = BinanceClient(settings.BINANCE_CLIENT)
        result, is_ok = client.get_symbols()

        if not is_ok:
            messages.error(request, 'Нет соединения с Binance')
            meta = self.model._meta
            url = reverse(
                f'admin:{meta.app_label}_{meta.model_name}_changelist'
            )
            return HttpResponseRedirect(url)

        for item in result:
            TradingPair.objects.update_or_create(
                symbol=item['symbol'],
                defaults={
                    'binance_id': item['id'],
                    'base': item['base'],
                    'quote': item['quote'],
                    'is_margin_trade': item['isMarginTrade'],
                    'is_buy_allowed': item['isBuyAllowed'],
                    'is_sell_allowed': item['isSellAllowed'],
                },
            )

        messages.success(request, 'Запущено обновление торговых пар')
        meta = self.model._meta
        url = reverse(f'admin:{meta.app_label}_{meta.model_name}_changelist')
        return HttpResponseRedirect(url)
