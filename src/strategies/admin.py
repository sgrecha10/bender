from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from indicators.models import MovingAverage, StandardDeviation
from market_data.models import Kline
from .models import Strategy, StrategyResult
from core.utils.admin_utils import redirect_to_change_form
from django.shortcuts import HttpResponse, render, redirect
from urllib.parse import urlencode
from .constants import CODENAME_MAP


class IndicatorInlineBaseAdmin(admin.TabularInline):
    extra = 0
    readonly_fields = ('pk', 'codename')


class MovingAverageInlineAdmin(IndicatorInlineBaseAdmin):
    classes = ('grp-collapse grp-open',)
    model = MovingAverage
    fields = (
        'pk',
        'codename',
        'symbol',
        'interval',
        'data_source',
        'type',
        'kline_count',
        'factor_alfa',
        'factor_alfa_auto',
    )
    raw_id_fields = ('symbol',)


class StandardDeviationInlineAdmin(IndicatorInlineBaseAdmin):
    classes = ('grp-collapse grp-open',)
    model = StandardDeviation
    fields = (
        'pk',
        'codename',
        'moving_average',
        'data_source',
        'kline_count',
    )


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    change_form_template = 'admin/strategies/change_form.html'

    list_display = (
        'id',
        'codename',
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
        'ratio_display',
    )
    inlines = (
        MovingAverageInlineAdmin,
        StandardDeviationInlineAdmin,
    )
    raw_id_fields = ('base_symbol',)
    list_display_links = ('codename',)

    fieldsets = (
        ('Основное', {
            'fields': (
                'codename',
                'description',
                'base_symbol',
                'base_interval',
                'start_time',
                'end_time',
            ),
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Риск-менеджмент', {
            'fields': (
                'stop_loss_factor',
                'take_profit_factor',
                'ratio_display',
                'fixed_bet_amount',
            ),
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Информация', {
            'fields': (
                'created',
                'updated',
            ),
            # 'classes': ('grp-collapse grp-open',),
        }),
    )

    def response_change(self, request, obj):
        if '_run-strategy' in request.POST:
            """ Запускаем тестирование стратегии 
            
            Для запуска стратегии в рабочий режим надо будет еще подумать.
            """

            StrategyResult.objects.filter(strategy_id=obj.id).delete()

            # получаем бекенд стратегии
            backend = CODENAME_MAP[obj.codename]()

            # получаем df для тестирования
            kline_qs = Kline.objects.filter(
                symbol=obj.base_symbol,
                open_time__gte=obj.start_time,
                open_time__lte=obj.end_time,
            )
            kline_df = kline_qs.group_by_interval().to_dataframe(index='open_time_group')

            # обходим полученный df начиная с самой старой свечи
            last_kline = None
            last_idx = None
            for idx, kline_item in kline_df.iterrows():
                # потому что тестирование
                backend.check_price(
                    idx=idx,
                    price=kline_item['high_price'],
                )
                backend.check_price(
                    idx=idx,
                    price=kline_item['low_price'],
                )
                last_kline = kline_item
                last_idx = idx

            backend.close_all_position(idx=last_idx, price=last_kline['close_price'])

            message = 'Finished'
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
        instance = self.model.objects.get(pk=kwargs['id'])
        data = {
            'symbol': instance.base_symbol.symbol,
            'interval': instance.base_interval,
            'start_time_0': instance.start_time.strftime('%d.%m.%Y'),
            'start_time_1': instance.start_time.strftime('%H:%M'),
            'end_time_0': instance.end_time.strftime('%d.%m.%Y'),
            'end_time_1': instance.end_time.strftime('%H:%M'),
            'strategy': instance.id,
            'volume': True,
        }

        url = reverse('chart') + '?' + urlencode(data)
        return redirect(url)

    @admin.display(description='Ratio')
    def ratio_display(self, request, *args, **kwargs):
        return round(request.take_profit_factor / request.stop_loss_factor, 3)


@admin.register(StrategyResult)
class StrategyResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'strategy',
        'kline',
        'buy',
        'sell',
        'created',
        'updated',
    )
    list_filter = (
        'strategy',
    )
    raw_id_fields = (
        'kline',
    )
    actions = (
        'trunkate_strategy_result',
    )

    @admin.action(description='Очистить всю таблицу')
    def trunkate_strategy_result(self, request, *args, **kwargs):
        self.model.objects.all().delete()
