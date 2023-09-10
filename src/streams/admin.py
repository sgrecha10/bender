from django.contrib import admin
from .models import TaskManagement, DepthOfMarket
from core.utils.admin_utils import redirect_to_change_list


@admin.register(TaskManagement)
class TaskManagementAdmin(admin.ModelAdmin):
    list_display = ('codename', 'is_working', 'updated', 'created')


@admin.register(DepthOfMarket)
class DepthOfMarketAdmin(admin.ModelAdmin):
    list_display = ('id', 'symbol', 'is_active', 'depth', 'updated', 'created')
    raw_id_fields = ('symbol',)
    actions = ('action_run', 'action_stop')

    @admin.action(description='Запустить глубину рынка')
    def action_run(self, request, query=None):
        symbols = [item.symbol for item in query]
        query.update(is_active=True)
        message = f'action_run {query}'
        is_ok = True
        return redirect_to_change_list(request, self.model, message, is_ok)

    @admin.action(description='Остановить глубину рынка')
    def action_stop(self, request, query=None):
        symbols = [item.symbol for item in query]
        query.update(is_active=False)
        message = f'action_stop {symbols}'
        is_ok = False
        return redirect_to_change_list(request, self.model, message, is_ok)