from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path

from indicators.models import MovingAverage
from market_data.models import Kline
from .models import Strategy, StrategyResult
from core.utils.admin_utils import redirect_to_change_form
from django.shortcuts import HttpResponse, render


class IndicatorInlineBaseAdmin(admin.TabularInline):
    extra = 0
    readonly_fields = ('pk',)
    fields = (
        'pk',
        'codename',
        # 'description',
        'symbol',
        'interval',
        'data_source',
        'type',
        'kline_count',
        'factor_alfa',
        'factor_alfa_auto',

    )
    raw_id_fields = ('symbol',)
    # show_change_link = True


class MovingAverageInlineAdmin(IndicatorInlineBaseAdmin):
    model = MovingAverage


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    change_form_template = 'admin/strategies/change_form.html'
    chart_template = 'admin/strategies/strategy_chart.html'
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
        'base_interval',
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
            # пока для примера заполним StrategyResult:
            StrategyResult.objects.filter(strategy=obj).delete()

            kline_qs = Kline.objects.filter(
                symbol=obj.base_symbol,
                open_time__gte=obj.start_time,
                open_time__lte=obj.end_time,
            )
            for kline in kline_qs:
                StrategyResult.objects.create(
                    strategy=obj,
                    kline=kline,
                    price=kline.high_price + 500,
                )

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

    def show_strategy_result(self, request, *args, **kwargs):
        from market_data.forms import ChartForm
        form = ChartForm()

        context = {
            'opts': self.model._meta,
            'form': form,
        }
        return render(request, self.chart_template, context=context)


@admin.register(StrategyResult)
class StrategyResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'strategy',
        'kline',
        'price',
        'created',
        'updated',
    )
    list_filter = (
        'strategy',
    )
    raw_id_fields = (
        'kline',
    )
