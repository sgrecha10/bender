from django.contrib import admin
from django.urls import path

from core.utils.admin_utils import redirect_to_change_list
from market_data.models import ExchangeInfo


@admin.register(ExchangeInfo)
class ExchangeInfoAdmin(admin.ModelAdmin):
    change_list_template = "admin/market_data/exchange_info/change_list.html"
    list_display = ('id', 'symbol', 'updated')
    actions = ('action_update_exchange_info',)

    # def has_add_permission(self, request):
    #     return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.action(description='Обновить')
    def action_update_exchange_info(self, request, symbol_query=None):
        symbols = [item.symbol for item in symbol_query]
        self.update_exchange_info(request, symbols=symbols)

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path(
                'update_exchange_info/',
                self.update_exchange_info,
                name='update_exchange_info',
            ),
        ]
        return added_urls + urls

    def update_exchange_info(self, request, symbol=None, symbols=None, permissions=None):
        result, is_ok = self.model.get_update(symbol, symbols, permissions)
        message = f'Обновили {result} записей' if is_ok else result
        return redirect_to_change_list(request, self.model, message, is_ok)

    def save_model(self, request, obj, form, change):
        symbol = form.cleaned_data['symbol']
        if not change:
            self.model.get_update(symbol=symbol)
