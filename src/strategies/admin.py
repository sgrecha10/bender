from django.contrib import admin
from .models import Strategy, AveragePrice


class AveragePriceInlineAdmin(admin.TabularInline):
    model = AveragePrice
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
    )


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'symbol',
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
        AveragePriceInlineAdmin,
    )
    raw_id_fields = ('symbol',)


@admin.register(AveragePrice)
class AveragePriceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'codename',
        'value',
        'strategy',
        'updated',
        'created',
    )
    readonly_fields = (
        'updated',
        'created',
    )
