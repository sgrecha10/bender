from django.contrib import admin

from .models import (
    MovingAverage,
    StandardDeviation,
    BollingerBands,
)


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


@admin.register(StandardDeviation)
class StandardDeviationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'codename',
        'description',
        'moving_average',
        'data_source',
        'kline_count',
        'updated',
        'created',
    )
    list_display_links = ('codename',)
    list_editable = (
        'data_source',
        'kline_count',
    )
    readonly_fields = (
        'updated',
        'created',
    )


@admin.register(BollingerBands)
class BollingerBandsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'codename',
        'description',
        'moving_average',
        'standard_deviation',
        'sigma_factor',
        'updated',
        'created',
    )
    readonly_fields = (
        'updated',
        'created',
    )
