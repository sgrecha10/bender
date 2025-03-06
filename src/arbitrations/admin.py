from django.contrib import admin
from .models import Arbitration, ArbitrationDeal
from django.urls import path, reverse
from django.shortcuts import redirect
from urllib.parse import urlencode
from .tasks import run_arbitration_test_mode
from core.utils.admin_utils import redirect_to_change_form
from indicators.models import MovingAverage, StandardDeviation, BetaFactor


class MovingAverageInlineAdmin(admin.TabularInline):
    classes = ('grp-collapse grp-open',)
    extra = 0
    model = MovingAverage
    fields = (
        'pk',
        'codename',
        'description',
        'window_size',
        # 'interval',
        # 'price_comparison',
        # 'data_source',
        'type',
        # 'factor_alfa',
        # 'factor_alfa_auto',
        # 'symbol',
    )
    show_change_link = True
    readonly_fields = (
        'pk',
        'codename',
        'description',
        # 'symbol',
        'type',
    )


class StandardDeviationInlineAdmin(admin.TabularInline):
    classes = ('grp-collapse grp-open',)
    extra = 0
    model = StandardDeviation
    fields = (
        'pk',
        'codename',
        'description',
        'window_size',
        # 'interval',
        # 'price_comparison',
        # 'moving_average',
        # 'data_source',
    )
    show_change_link = True
    readonly_fields = (
        'pk',
        'codename',
        'description',
        # 'moving_average',
    )


class BetaFactorInlineAdmin(admin.TabularInline):
    classes = ('grp-collapse grp-open',)
    extra = 0
    model = BetaFactor
    fields = (
        'pk',
        'codename',
        'description',
        'window_size',
        # 'interval',
        # 'price_comparison',
        'market_symbol',
        'type',
        'ema_span',
        # 'variance_price_comparison',
        # 'covariance_price_comparison',
        # 'butterworth_order',
        # 'butterworth_cutoff',
    )
    show_change_link = True
    readonly_fields = (
        'pk',
        'codename',
        'description',
    )


@admin.register(Arbitration)
class ArbitrationAdmin(admin.ModelAdmin):
    change_form_template = 'admin/arbitrations/change_form.html'
    inlines = (
        MovingAverageInlineAdmin,
        StandardDeviationInlineAdmin,
        BetaFactorInlineAdmin,
    )
    list_display = (
        'id',
        'codename',
        'symbol_1',
        'symbol_2',
        'interval',
        'start_time',
        'end_time',
    )
    raw_id_fields = (
        'symbol_1',
        'symbol_2',
    )
    readonly_fields = (
        'updated',
        'created',
    )
    list_display_links = ('codename',)
    fieldsets = [
        ('Основное', {
            'fields': [
                'codename',
                'symbol_1',
                'symbol_2',
                'interval',
                'price_comparison',
                'data_source',
                'start_time',
                'end_time',

            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),

        ('Аналитика', {
            'fields': [
                'correlation_window',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),

        ('Условия открытия/закрытия сделок', {
            'fields': [
                'open_deal_sd',
                'close_deal_sd',
                'fixed_bet_amount',
                'ratio_type',
                'correction_type',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Настройки для теста', {
            'fields': [
                'entry_price_order',
                'maker_commission',
                'taker_commission',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Информация', {
            'fields': [
                'updated',
                'created',
            ],
        }),
    ]

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path(
                '<int:id>/show_chart/',
                self.show_chart,
                name='arbitration-show-chart',
            ),
            path(
                '<int:id>/test_run/',
                self.test_run,
                name='arbitration-test-run',
            ),
        ]
        return added_urls + urls

    def show_chart(self, request, *args, **kwargs):
        instance = self.model.objects.get(pk=kwargs['id'])
        data = {
            'arbitration': instance.id,
        }

        url = reverse('arbitration-chart') + '?' + urlencode(data)
        return redirect(url)

    def test_run(self, request, *args, **kwargs):
        run_arbitration_test_mode(arbitration_id=kwargs['id'])
        message = 'Run arbitration test mode started..'
        return redirect_to_change_form(request, self.model, kwargs['id'], message)


@admin.register(ArbitrationDeal)
class ArbitrationDealAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'arbitration',
        'symbol',
        'deal_uid',
        'deal_time',
        'price',
        'quantity',
        'display_direction',
        'beta_quantity_1',
        'beta_quantity_2',
        'buy',
        'sell',
        'state',
        'updated',
        'created',
    )
    readonly_fields = (
        'server_time',
        'updated',
        'created',
    )

    @admin.display(description='Direction')
    def display_direction(self, obj):
        if obj.quantity:
            return 'LONG' if obj.quantity < 0 else 'SHORT'
