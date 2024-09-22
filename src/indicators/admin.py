from django.contrib import admin

from .models import MovingAverage


@admin.register(MovingAverage)
class MovingAverageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'codename',
        'description',
        'symbol',
        'interval',
        'data_source',
        'type',
        'kline_count',
        'factor_alfa',
        'factor_alfa_auto',
        'strategy',
        'updated',
        'created',
    )
    list_display_links = ('id', 'codename')
    raw_id_fields = ('symbol',)
    list_editable = (
        'interval',
        'data_source',
        'kline_count',
    )
    readonly_fields = (
        'updated',
        'created',
    )
