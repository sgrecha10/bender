from django.contrib import admin
from .models import TaskManagement


@admin.register(TaskManagement)
class TaskManagementAdmin(admin.ModelAdmin):
    list_display = ('codename', 'is_working', 'updated', 'created')
