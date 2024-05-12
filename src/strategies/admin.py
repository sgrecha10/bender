from django.contrib import admin
from .models import Strategy, AveragePrice


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
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


@admin.register(AveragePrice)
class AveragePriceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'codename',
        'value',
        'strategy',
    )
