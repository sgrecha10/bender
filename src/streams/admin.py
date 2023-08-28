from django.contrib import admin
from .models import StreamTest


@admin.register(StreamTest)
class StreamTestAdmin(admin.ModelAdmin):
    pass
