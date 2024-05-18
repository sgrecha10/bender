from django.contrib import admin

from indicators.models import AveragePrice, MovingAverage
from .models import Strategy


class IndicatorInlineBaseAdmin(admin.TabularInline):
    extra = 0
    fields = (
        'id',
        'name',
        'codename',
        'value',
        'description',
    )
    readonly_fields = (
        'name',
        'codename',
        'description',
    )

    def has_add_permission(self, *_):
        return False


class AveragePriceInlineAdmin(IndicatorInlineBaseAdmin):
    model = AveragePrice


class MovingAverageInlineAdmin(IndicatorInlineBaseAdmin):
    model = MovingAverage


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'symbol',
        'interval',
        'is_active',
        'status',
        'updated',
        'created',
    )
    readonly_fields = (
        'is_active',
        'created',
        'updated',
    )
    inlines = (
        MovingAverageInlineAdmin,
        AveragePriceInlineAdmin,
    )
    raw_id_fields = ('symbol',)
