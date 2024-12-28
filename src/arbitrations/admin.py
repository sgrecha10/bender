from django.contrib import admin
from .models import Arbitration


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
    ]
