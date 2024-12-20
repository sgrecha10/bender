from django.contrib import admin
from .models import Arbitration


@admin.register(Arbitration)
class ArbitrationAdmin(admin.ModelAdmin):
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
