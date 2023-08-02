from django.contrib import admin
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.urls import path, reverse

from .models import TradingPair


@admin.register(TradingPair)
class TradingPairAdmin(admin.ModelAdmin):
    change_list_template = "admin/trading_pairs/trading_pair/change_list.html"
    list_display = (
        'id', 'symbol', 'binance_id', 'base', 'quote', 'is_margin_trade',
        'is_buy_allowed', 'is_sell_allowed', 'updated', 'created',
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
        messages.success(
            request, 'Запущено обновление торговых пар'
        )
        meta = self.model._meta
        url = reverse(f'admin:{meta.app_label}_{meta.model_name}_changelist')
        return HttpResponseRedirect(url)
