from django.db import models


class TradingPair(models.Model):
    binance_id = models.CharField(
        verbose_name='Binance ID',
        max_length=100,
        unique=True,
    )
    symbol = models.CharField(
        verbose_name='Идентификатор',
        max_length=50,
        unique=True,
    )
    base = models.CharField(
        verbose_name='Основание',
        max_length=50,
    )
    quote = models.CharField(
        verbose_name='Котировка',
        max_length=50,
    )
    is_margin_trade = models.BooleanField(
        verbose_name='Маржинальная торговля',
        default=False,
    )
    is_buy_allowed = models.BooleanField(
        verbose_name='Разрешена покупка',
        default=False,
    )
    is_sell_allowed = models.BooleanField(
        verbose_name='Разрешена продажа',
        default=False,
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
        verbose_name = 'Кросс-пара'
        verbose_name_plural = 'Кросс-пары'

    def __str__(self):
        return self.symbol
