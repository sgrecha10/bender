import os

from celery import Celery
from django.conf import settings
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bender.settings")
app = Celery(__name__, broker=settings.BROKER_URL)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


app.conf.beat_schedule.update({
    'periodic_debug_task': {
        'task': 'wallet.tasks.debug_task',
        'schedule': crontab(),
    },
})
