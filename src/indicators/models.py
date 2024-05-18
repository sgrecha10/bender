from django.db import models
from core.utils.db_utils import BaseModel
from strategies.models import Strategy


class IndicatorBase(BaseModel):
    strategy = models.ForeignKey(
        Strategy, on_delete=models.PROTECT,
        verbose_name='Strategy',
        blank=True, null=True,
    )
    name = models.CharField(
        verbose_name='Name',
        max_length=255,
    )
    codename = models.CharField(
        verbose_name='Codename',
        max_length=100,
    )
    value = models.CharField(
        verbose_name='Value',
        max_length=255,
    )
    description = models.TextField(
        verbose_name='Description',
        blank=True, null=True,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class MovingAverage(IndicatorBase):
    class Meta:
        verbose_name = 'MovingAverage'
        verbose_name_plural = 'MovingAverage'
        unique_together = ('strategy', 'codename')


class AveragePrice(IndicatorBase):
    class Meta:
        verbose_name = 'AveragePrice'
        verbose_name_plural = 'AveragePrice'
        unique_together = ('strategy', 'codename')
