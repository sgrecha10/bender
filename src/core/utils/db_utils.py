from django.db import models


class BaseModel(models.Model):
    server_time = models.BigIntegerField(
        verbose_name='serverTime',
        null=True, blank=True, default=None,
    )
    updated = models.DateTimeField(
        verbose_name='Дата обновления',
        auto_now=True,
    )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
    )

    class Meta:
        abstract = True
