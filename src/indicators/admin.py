from django.contrib import admin
from .models import AveragePrice, MovingAverage
from django.contrib import messages
from django.urls import reverse
from django.db import IntegrityError
from django.shortcuts import redirect


class IndicatorBaseAdmin(admin.ModelAdmin):
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
        'copy_item',
    )

    @admin.action(description='Copy %(verbose_name_plural)s')
    def copy_item(self, request, queryset):
        try:
            model_item = queryset.get()
        except (queryset.model.DoesNotExist, queryset.model.MultipleObjectsReturned):
            messages.error(request, 'Only one item needed.')
            return

        queryset.model.objects.create(
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
            app_label, model_name = self.model._meta.app_label, self.model._meta.model_name
            url = reverse(f'admin:{app_label}_{model_name}_changelist')
            return redirect(url)


@admin.register(AveragePrice)
class AveragePriceAdmin(IndicatorBaseAdmin):
    pass


@admin.register(MovingAverage)
class MovingAverageAdmin(IndicatorBaseAdmin):
    pass
