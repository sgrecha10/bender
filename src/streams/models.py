from django.db import models
from core.utils.db_utils import BaseModel
import uuid
from market_data.models import ExchangeInfo


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


class DepthOfMarket(BaseModel):
    symbol = models.ForeignKey(
        ExchangeInfo, on_delete=models.CASCADE,
        verbose_name='Symbol',
    )
    is_active = models.BooleanField(
        verbose_name='Status',
        default=False,
    )
    depth = models.PositiveSmallIntegerField(
        verbose_name='Depth',
        default=100,
    )

    class Meta:
        verbose_name = 'Глубина рынка'
        verbose_name_plural = 'Глубина рынка'

    def __str__(self):
        return self.symbol.symbol
