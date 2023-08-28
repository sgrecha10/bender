from django.db import models
from core.utils.db_utils import BaseModel


class StreamTest(BaseModel):
    result = models.TextField(
        verbose_name='result',
    )

    class Meta:
        verbose_name = 'StreamTest'
        verbose_name_plural = 'StreamTest'

    def __str__(self):
        return f'{self.id}'
