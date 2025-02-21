from django.contrib import admin

from .forms import StandardDeviationForm
from .models import (
    MovingAverage,
    StandardDeviation,
    BollingerBands,
    BetaFactor,
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
        'window_size',
        'factor_alfa',
        'factor_alfa_auto',
        'strategy',
        'arbitration',
        'updated',
        'created',
    )
    list_display_links = ('id', 'codename')
    raw_id_fields = ('symbol',)
    list_editable = (
        'interval',
        'data_source',
        'window_size',
    )
    readonly_fields = (
        'updated',
        'created',
    )


@admin.register(StandardDeviation)
class StandardDeviationAdmin(admin.ModelAdmin):
    form = StandardDeviationForm
    list_display = (
        'id',
        'codename',
        'description',
        'moving_average',
        'data_source',
        'window_size',
        'strategy',
        'arbitration',
        'updated',
        'created',
    )
    list_display_links = ('codename',)
    list_editable = (
        'data_source',
        'window_size',
    )
    readonly_fields = (
        'updated',
        'created',
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        return form


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


@admin.register(BetaFactor)
class BetaFactorAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'codename',
        'window_size',
        'variance_price_comparison',
        'covariance_price_comparison',
        'arbitration',
        'interval',
        'updated',
        'created',
    )
    readonly_fields = (
        'updated',
        'created',
    )
