from django.db import models
from core.utils.db_utils import BaseModel
from market_data.models import ExchangeInfo


class Strategy(BaseModel):
    class Status(models.IntegerChoices):
        STOPPED = 0, 'Stopped'
        ACTIVE = 1, 'Active'
        TESTING = 2, 'Testing'

    codename = models.CharField(
        verbose_name='Codename',
        max_length=100,
        unique=True,
    )
    name = models.CharField(
        verbose_name='Name',
        max_length=255,
    )
    symbol = models.ForeignKey(
        ExchangeInfo,
        on_delete=models.CASCADE,
        verbose_name='Symbol',
        null=True,
        blank=True,
    )
    status = models.PositiveSmallIntegerField(
        verbose_name='Status',
        choices=Status.choices,
        default=Status.STOPPED,
    )
    is_active = models.BooleanField(
        verbose_name='Active',
        default=False,
    )

    class Meta:
        verbose_name = 'Strategy'
        verbose_name_plural = 'Strategies'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.is_active = False if self.status == Strategy.Status.STOPPED else True
        super().save(*args, **kwargs)


class AveragePrice(BaseModel):
    strategy = models.ForeignKey(
        Strategy, on_delete=models.PROTECT,
        verbose_name='Strategy',
    )
    name = models.CharField(
        verbose_name='Name',
        max_length=255,
    )
    codename = models.CharField(
        verbose_name='Codename',
        max_length=100,
        unique=True,
    )
    value = models.CharField(
        verbose_name='Value',
        max_length=255,
    )
    description = models.TextField(
        verbose_name='Description',
    )

    class Meta:
        verbose_name = 'AveragePrice'
        verbose_name_plural = 'AveragePrice'

    def __str__(self):
        return self.name
