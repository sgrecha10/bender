from django.db import models
from core.utils.db_utils import BaseModel


class UniswapPool(BaseModel):
    class PoolType(models.TextChoices):
        UNISWAP_V1 = 'UNISWAP_V1', ' Uniswap V1'
        UNISWAP_V2 = 'UNISWAP_V2', ' Uniswap V2'
        UNISWAP_V3 = 'UNISWAP_V3', ' Uniswap V3'
        UNISWAP_V4 = 'UNISWAP_V4', ' Uniswap V4'

    pool_address = models.CharField(
        primary_key=True,
        max_length=42,
        verbose_name='Pool Address',
    )
    pool_type = models.CharField(
        choices=PoolType.choices,
        null=True,
        blank=True,
        verbose_name='Pool Type',
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
        return f'{self.pool_type} - {self.pool_address}'


class Transaction(BaseModel):
    tx_hash = models.CharField(
        primary_key=True,
        max_length=255,
        verbose_name='Transaction Hash',
    )
    block_hash = models.CharField(
        null=True,
        max_length=255,
        verbose_name='Block Hash',
    )
    block_number = models.PositiveBigIntegerField(
        null=True,
        verbose_name='Block Number',
    )
    from_address = models.CharField(
        null=True,
        max_length=42,
        verbose_name='From',
    )
    to_address = models.CharField(
        null=True,
        max_length=42,
        verbose_name='To',
    )
    value = models.TextField(
        null=True,
        verbose_name='Value',
    )
    gas = models.TextField(
        null=True,
        verbose_name='Gas',
    )
    input = models.TextField(
        null=True,
        verbose_name='Input',
    )
    nonce = models.PositiveBigIntegerField(
        null=True,
        verbose_name='Nonce',
    )
    tx_index = models.PositiveIntegerField(
        null=True,
        verbose_name='Transaction Index',
    )
    gas_price = models.TextField(
        null=True,
        verbose_name='gasPrice',
    )
    max_fee_per_gas = models.TextField(
        null=True,
        verbose_name='maxFeePerGas',
    )
    max_priority_fee_per_gas = models.TextField(
        null=True,
        verbose_name='maxPriorityFeePerGas',
    )
    type = models.PositiveSmallIntegerField(
        null=True,
        verbose_name='Type',
    )
    chain_id = models.PositiveBigIntegerField(
        null=True,
        verbose_name='ChainId',
    )
    y_parity = models.PositiveSmallIntegerField(
        null=True,
        verbose_name='yParity',
    )
    access_list = models.TextField(
        null=True,
        verbose_name='Access List',
    )

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'

    def __str__(self):
        return self.tx_hash


class SwapChain(BaseModel):
    codename = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Codename',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Name',
    )
    pool_0 = models.ForeignKey(
        UniswapPool,
        on_delete=models.CASCADE,
        null=True,
        related_name='pool_0',
        verbose_name='Pool 0',
    )
    pool_1 = models.ForeignKey(
        UniswapPool,
        on_delete=models.CASCADE,
        null=True,
        related_name='pool_1',
        verbose_name='Pool 1',
    )

    class Meta:
        verbose_name = 'Swap Chain'
        verbose_name_plural = 'Swap Chains'

    def __str__(self):
        return str(self.id)


class ERC20Token(BaseModel):
    address = models.CharField(
        primary_key=True,
        max_length=42,
        verbose_name='Address',
    )
    name = models.CharField(
        null=True,
        max_length=100,
        verbose_name='Name',
    )
    symbol = models.CharField(
        null=True,
        max_length=50,
        verbose_name='Symbol',
    )
    decimals = models.PositiveSmallIntegerField(
        null=True,
        verbose_name='Decimals',
    )
    total_supply = models.CharField(
        null=True,
        max_length=255,
        verbose_name='Total Supply',
    )
    owner = models.CharField(
        null=True,
        max_length=42,
        verbose_name='Owner',
    )
    version = models.CharField(
        null=True,
        max_length=50,
        verbose_name='Version',
    )
    domain_separator = models.CharField(
        null=True,
        max_length=255,
        verbose_name='Domain Separator',
    )

    class Meta:
        verbose_name = 'ERC-20 Token'
        verbose_name_plural = 'ERC-20 Tokens'

    def __str__(self):
        return f'ERC20 {self.pk}'
