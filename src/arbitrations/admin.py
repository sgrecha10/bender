from django.contrib import admin
from .models import Arbitration, ArbitrationDeal
from django.urls import path, reverse
from django.shortcuts import redirect
from urllib.parse import urlencode
from .tasks import run_arbitration_test_mode
from core.utils.admin_utils import redirect_to_change_form


@admin.register(Arbitration)
class ArbitrationAdmin(admin.ModelAdmin):
    change_form_template = 'admin/arbitrations/change_form.html'
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
        ('Main', {
            'fields': [
                'codename',
                'symbol_1',
                'symbol_2',
                'interval',
                'start_time',
                'end_time',

            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Difference', {
            'fields': [
                'price_comparison',
                'moving_average',
                'standard_deviation',

            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Conditions deal', {
            'fields': [
                'open_deal_sd',
                'close_deal_sd',
                'fixed_bet_amount',
                'ratio_type',
                'b_factor_window',
                'b_factor_price_comparison',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Conditions test', {
            'fields': [
                'entry_price_order',
                'maker_commission',
                'taker_commission',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Information', {
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
        'deal_time',
        'price',
        'quantity',
        'display_direction',
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
