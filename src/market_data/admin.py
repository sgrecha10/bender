from django.contrib import admin
from django.urls import path

from core.utils.admin_utils import redirect_to_change_list
from market_data.models import ExchangeInfo, Kline, Interval
from django.forms import ALL_FIELDS
from django.template.response import TemplateResponse
from .forms import MiddlePageForm


@admin.register(ExchangeInfo)
class ExchangeInfoAdmin(admin.ModelAdmin):
    change_list_template = "admin/market_data/exchange_info/change_list.html"
    list_display = ('id', 'symbol', 'status', 'updated')
    actions = ('action_update_exchange_info',)
    list_filter = ('status', 'base_asset', 'quoteAsset')
    search_fields = ('symbol',)

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


@admin.register(Kline)
class KlineAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'symbol',
        'open_time',
        'open_price',
        'high_price',
        'low_price',
        'close_price',
        'volume',
        'close_time',
    )
    change_list_template = "admin/market_data/kline/change_list.html"
    middle_page_template = "admin/market_data/kline/middle_page.html"

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path(
                'get_kline/',
                self.admin_site.admin_view(self.get_kline),
                name='get_kline',
            ),
        ]
        return added_urls + urls

    def get_kline(self, request):
        if 'apply' in request.POST:
            form = MiddlePageForm(request.POST)

            # result, is_ok = self.model.get_update(symbol, symbols, permissions)
            # message = f'Обновили {result} записей' if is_ok else result
            message = 'grecha'
            is_ok = True
            return redirect_to_change_list(request, self.model, message, is_ok)

        else:
            form = MiddlePageForm()
            return TemplateResponse(request, self.middle_page_template, {'form': form})


@admin.register(Interval)
class IntervalAdmin(admin.ModelAdmin):
    list_display = (
        'codename',
        'value',
    )
