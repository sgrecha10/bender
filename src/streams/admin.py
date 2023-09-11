from django.contrib import admin
from .models import TaskManagement, DepthOfMarket, TrainingData
from core.utils.admin_utils import redirect_to_change_list
from django.utils.safestring import mark_safe
from streams.handlers.depth_of_market import DepthOfMarketStream, DepthOfMarketStreamError


@admin.register(TaskManagement)
class TaskManagementAdmin(admin.ModelAdmin):
    list_display = ('codename', 'is_working', 'updated', 'created')


@admin.register(DepthOfMarket)
class DepthOfMarketAdmin(admin.ModelAdmin):
    list_display = ('id', 'symbol', 'is_active', 'depth', 'market_glass', 'updated', 'created')
    raw_id_fields = ('symbol',)
    actions = ('action_run', 'action_stop')
    ordering = ('-is_active', 'id')

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='Market glass')
    def market_glass(self, obj):
        return mark_safe(f'<a href="" target="_blank">открыть</a>')

    @admin.action(description='Запустить "Глубину рынка"')
    def action_run(self, request, query=None):
        msg = []
        status = True
        for dom in query:
            try:
                dom_stream = DepthOfMarketStream(dom.symbol.symbol, dom.depth)
                dom_stream.run()
                dom.is_active = True
                dom.save(update_fields=['is_active'])
            except DepthOfMarketStreamError as e:
                msg.append(e.msg)
                status = False
        message = msg, status

        return redirect_to_change_list(request, self.model, message)

    @admin.action(description='Остановить "Глубину рынка"')
    def action_stop(self, request, query=None):
        msg = []
        status = True
        for dom in query:
            try:
                dom_stream = DepthOfMarketStream(dom.symbol.symbol, dom.depth)
                dom_stream.stop()
                dom.is_active = False
                dom.save(update_fields=['is_active'])
            except DepthOfMarketStreamError as e:
                msg.append(e.msg)
                status = False
        message = msg, status

        return redirect_to_change_list(request, self.model, message)


@admin.register(TrainingData)
class TrainingDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'depth_of_market', 'is_active', 'amount', 'depth', 'market_glass', 'updated', 'created')
    actions = ('action_run', 'action_stop')

    # def has_add_permission(self, request):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='Market glass')
    def market_glass(self, obj):
        return mark_safe(f'<a href="" target="_blank">открыть</a>')

    @admin.action(description='Запустить "Тестовые данные"')
    def action_run(self, request, query=None):
        # symbols = [item.symbol for item in query]
        query.update(is_active=True)
        message = f'action_run {query}', True
        return redirect_to_change_list(request, self.model, message)

    @admin.action(description='Остановить "Тестовые данные"')
    def action_stop(self, request, query=None):
        # symbols = [item.symbol for item in query]
        query.update(is_active=False)
        message = f'action_stop {query}', False
        return redirect_to_change_list(request, self.model, message)