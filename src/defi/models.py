from django.db import models
from core.utils.db_utils import BaseModel


class UniswapPool(BaseModel):
    class PoolType(models.TextChoices):
        UNISWAP_V1 = 'UNISWAP_V1', ' Uniswap V1'
        UNISWAP_V2 = 'UNISWAP_V2', ' Uniswap V2'
        UNISWAP_V3 = 'UNISWAP_V3', ' Uniswap V3'
        UNISWAP_V4 = 'UNISWAP_V4', ' Uniswap V4'

    pool_type = models.CharField(
        choices=PoolType.choices,
        null=True,
        blank=True,
        verbose_name='Pool Type',
    )
    pool_address = models.CharField(
        null=True,
        blank=True,
        max_length=42,
        verbose_name='Pool Address',
    )
    token_0_address = models.CharField(
        null=True,
        blank=True,
        max_length=42,
        verbose_name='Token 0 Address',
    )
    token_1_address = models.CharField(
        null=True,
        blank=True,
        max_length=42,
        verbose_name='Token 1 Address',
    )
    fee = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Fee',
    )
    tick_spacing = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tick Spacing',
        help_text=(
            'tickSpacing — это ключевой параметр пула, который определяет шаг '
            'между доступными "тиками" цен (price ticks), на которых можно размещать ликвидность.'
        )
    )
    block_hash = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name='Block Hash',
    )
    block_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Block Number',
    )
    block_timestamp = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='Block Timestamp',
    )
    transaction_hash = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name='Transaction Hash',
    )
    transaction_index = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Transaction Index',
    )
    log_index = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Log Index',
    )
    removed = models.BooleanField(
        null=True,
        verbose_name='Removed',
    )

    class Meta:
        verbose_name = 'Uniswap Pool'
        verbose_name_plural = 'Uniswap Pools'

    def __str__(self):
        return f'{self.id} - {self.pool_type} - {self.pool_address}'
