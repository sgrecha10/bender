from django.contrib import admin
from .models import MovingAverage
from django.contrib import messages
from django.urls import reverse
from django.db import IntegrityError
from django.shortcuts import redirect
from django.forms.models import model_to_dict


class IndicatorBaseAdmin(admin.ModelAdmin):
    readonly_fields = (
        'updated',
        'created',
    )
    # actions = (
    #     'copy_item',
    # )

    # @admin.action(description='Copy %(verbose_name_plural)s')
    # def copy_item(self, request, queryset):
    #     try:
    #         model_item = queryset.get()
    #     except (queryset.model.DoesNotExist, queryset.model.MultipleObjectsReturned):
    #         messages.error(request, 'Only one item needed.')
    #         return
    #     model_dict = model_to_dict(model_item)
    #     queryset.model.objects.create(**model_dict)
    #     messages.success(request, 'Successfully copied.')

    # def changelist_view(self, request, extra_context=None):
    #     try:
    #         return super().changelist_view(request, extra_context)
    #     except IntegrityError:
    #         self.message_user(request, 'There is a bind: strategy, codename.', messages.ERROR)
    #         app_label, model_name = self.model._meta.app_label, self.model._meta.model_name
    #         url = reverse(f'admin:{app_label}_{model_name}_changelist')
    #         return redirect(url)


@admin.register(MovingAverage)
class MovingAverageAdmin(IndicatorBaseAdmin):
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
