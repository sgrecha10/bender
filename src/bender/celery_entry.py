import os

from celery import Celery
from django.conf import settings
from celery.schedules import crontab
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bender.settings")
app = Celery(__name__, broker=settings.BROKER_URL)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


if settings.PERIODIC_CELERY_TASKS_DEBUG:
    app.conf.beat_schedule.update(
        {
            'periodic_debug_task': {
                'task': 'wallet.tasks.debug_task',
                'schedule': 1.0,
            },
        }
    )


if settings.STRATEGY_ID:
    app.conf.beat_schedule.update(
        {
            'periodic_trade_task': {
                'task': 'liquidity_pools.tasks.periodic_trade_task',
                'schedule': timedelta(minutes=1),  # timedelta(minutes=1)  crontab(minute='*')
            }
        }
    )
