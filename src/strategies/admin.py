from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path

from indicators.models import MovingAverage
from .models import Strategy
from core.utils.admin_utils import redirect_to_change_form
from django.shortcuts import HttpResponse


class IndicatorInlineBaseAdmin(admin.TabularInline):
    extra = 0
    fields = (
        'id',
        'name',
        'description',
        'data_source',
        'type',
        'kline_count',
        'factor_alfa',
        'factor_alfa_auto',
        'symbol',
        'interval',
    )
    raw_id_fields = ('symbol',)


class MovingAverageInlineAdmin(IndicatorInlineBaseAdmin):
    model = MovingAverage


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    change_form_template = 'admin/strategies/change_form.html'
    list_display = (
        'id',
        'name',
        'description',
        'base_symbol',
        'base_interval',
        'start_time',
        'end_time',
        'updated',
        'created',
    )
    readonly_fields = (
        'created',
        'updated',
    )
    inlines = (
        MovingAverageInlineAdmin,
    )
    raw_id_fields = ('base_symbol',)
    list_display_links = ('id', 'name')

    def response_change(self, request, obj):
        if "_run-strategy" in request.POST:
            # здесь главный метод стратегии (выбирать по айди)
            message = 'Run'
            return redirect_to_change_form(request, self.model, obj.id, message)
        else:
            return super().response_change(request, obj)

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path(
                '<int:id>/show_strategy_result/',
                self.show_strategy_result,
                name='show_strategy_result',
            ),
        ]
        return added_urls + urls

    def show_strategy_result(self, *args, **kwargs):
        return HttpResponse('anna')

# @admin.register(StrategyResult)
# class StrategyResultAdmin(admin.ModelAdmin):
#     list_display = (
#         'id',
#         'strategy',
#         'kline',
#         'price',
#         'created',
#         'updated',
#     )
#     list_filter = (
#         'strategy',
#     )
#     raw_id_fields = (
#         'kline',
#     )
