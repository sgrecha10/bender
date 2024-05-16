from django.contrib import admin
from django.http import Http404

from .models import Strategy, AveragePrice
from django.contrib import messages
from django.shortcuts import redirect
from django.db import IntegrityError
from django.urls import reverse


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
        'description',
    )

    def has_add_permission(self, *_):
        return False


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
    list_editable = ('strategy',)
    list_filter = ('strategy',)
    actions = (
        'copy_average_price',
    )

    @admin.action(description='Copy AveragePrice')
    def copy_average_price(self, request, queryset):
        try:
            model_item = queryset.get()
        except (queryset.model.DoesNotExist, AveragePrice.MultipleObjectsReturned):
            messages.error(request, 'Only one item needed.')
            return

        AveragePrice.objects.create(
            name=model_item.name,
            codename=model_item.codename,
            value=model_item.value,
            description=model_item.description,
        )
        messages.success(request, 'Successfully copied.')

    def changelist_view(self, request, extra_context=None):
        try:
            return super().changelist_view(request, extra_context)
        except IntegrityError:
            self.message_user(request, 'There is a bind: strategy, codename.', messages.ERROR)
            url = reverse('admin:strategies_averageprice_changelist')
            return redirect(url)
