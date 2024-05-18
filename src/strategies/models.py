from django.db import models
from core.utils.db_utils import BaseModel
from market_data.models import ExchangeInfo
from strategies.choices import Interval


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
    interval = models.CharField(
        verbose_name='Interval',
        choices=Interval.choices,
        max_length=5,
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
