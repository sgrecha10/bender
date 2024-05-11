from django.contrib import admin
from .models import Strategy, StrategyCommonVars


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


@admin.register(StrategyCommonVars)
class StrategyCommonVarsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'codename',
        'value',
        'group',
    )
