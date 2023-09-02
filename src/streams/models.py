from django.db import models
from core.utils.db_utils import BaseModel
import uuid


class TaskManagement(BaseModel):
    codename = models.CharField(
        verbose_name='codename',
        max_length=150,
        primary_key=True,
    )
    is_working = models.BooleanField(
        verbose_name='is_working',
        default=False,
    )

    class Meta:
        verbose_name = 'Управление задачей'
        verbose_name_plural = 'Управление задачами'

    def __str__(self):
        return self.codename
