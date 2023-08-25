from django.contrib import admin
from market_data.models import ExchangeInfo


@admin.register(ExchangeInfo)
class ExchangeInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'rate_limits')
    readonly_fields = list_display
