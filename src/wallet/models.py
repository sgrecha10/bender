from django.db import models


class Coin(models.Model):
    coin = models.CharField(
        verbose_name='coin',
        max_length=50,
        unique=True,
    )
    deposit_all_enable = models.BooleanField(
        verbose_name='depositAllEnable',
    )
    free = models.DecimalField(
        verbose_name='free',
        max_digits=12,
        decimal_places=10,
    )

    freeze = models.DecimalField(
        verbose_name='freeze',
        max_digits=12,
        decimal_places=10,
    )
    ipoable = models.DecimalField(
        verbose_name='ipoable',
        max_digits=12,
        decimal_places=10,
    )
    ipoing = models.DecimalField(
        verbose_name='ipoing',
        max_digits=12,
        decimal_places=10,
    )
    is_legal_money = models.BooleanField(
        verbose_name='isLegalMoney',
    )
    locked = models.DecimalField(
        verbose_name='locked',
        max_digits=12,
        decimal_places=10,
    )
    name = models.CharField(
        verbose_name='name',
        max_length=50,
    )
    storage = models.DecimalField(
        verbose_name='storage',
        max_digits=12,
        decimal_places=10,
    )
    trading = models.BooleanField(
        verbose_name='trading',
    )
    withdraw_all_enable = models.BooleanField(
        verbose_name='withdrawAllEnable',
    )
    withdrawing = models.DecimalField(
        verbose_name='withdrawing',
        max_digits=12,
        decimal_places=10,
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
        verbose_name = 'Монета'
        verbose_name_plural = 'Монеты'

    def __str__(self):
        return self.coin