from django.contrib import admin
from django.urls import path

from core.utils.admin_utils import redirect_to_change_list
from market_data.models import ExchangeInfo, Kline, Interval
from django.forms import ALL_FIELDS
from django.template.response import TemplateResponse
from .forms import GetKlineForm
from django.shortcuts import render
from .tasks import task_get_kline
from market_data.datetime_utils import datetime_to_timestamp


@admin.register(ExchangeInfo)
class ExchangeInfoAdmin(admin.ModelAdmin):
    change_list_template = "admin/market_data/exchange_info/change_list.html"
    list_display = ('symbol', 'status', 'updated')
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
        'display_open_time_timestamp',
        'open_price',
        'high_price',
        'low_price',
        'close_price',
        'volume',
        'close_time',
        'display_close_time_timestamp',
    )
    change_list_template = "admin/market_data/kline/change_list.html"
    get_kline_template = "admin/market_data/kline/get_kline_page.html"

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path(
                'get_kline/',
                self.admin_site.admin_view(self.get_kline),
                name='get_kline',
            ),
            path(
                'delete_from_table/',
                self.admin_site.admin_view(self.delete_from_table),
                name='delete_from_table',
            ),
        ]
        return added_urls + urls

    def get_kline(self, request):
        if request.method == "POST":
            form = GetKlineForm(request.POST)
            if form.is_valid():
                cleaned_data = form.cleaned_data

                task_get_kline.delay(
                    symbol=cleaned_data['symbol'].symbol,
                    interval=cleaned_data['interval'].value,
                    start_time=cleaned_data.get('start_time'),
                    end_time=cleaned_data.get('end_time'),
                    limit=cleaned_data.get('limit'),
                )

                message = 'Загрузка запущена.'
                return redirect_to_change_list(request, self.model, message)
        else:
            form = GetKlineForm()

        return render(request, self.get_kline_template, {'form': form})

    def delete_from_table(self, request):
        Kline.objects.all().delete()
        return redirect_to_change_list(request, self.model)

    @admin.display(description='open_time_timestamp', ordering='open_time')
    def display_open_time_timestamp(self, obj):
        return datetime_to_timestamp(obj.open_time)

    @admin.display(description='close_time_timestamp', ordering='close_time')
    def display_close_time_timestamp(self, obj):
        return datetime_to_timestamp(obj.close_time)


@admin.register(Interval)
class IntervalAdmin(admin.ModelAdmin):
    list_display = (
        'codename',
        'value',
        'minutes_count',
    )
