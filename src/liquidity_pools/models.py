from django.db import models


class BlockchainTransaction(models.Model):
    """Logging."""

    class TransactionType(models.TextChoices):
        SWAP = 'swap', 'Swap'
        MINT = 'mint', 'Mint'
        BURN = 'burn', 'Burn'
        COLLECT = 'collect', 'Collect'
        APPROVE = 'approve', 'Approve'
        DECREASE_LIQUIDITY = 'decrease_liquidity', 'Decrease Liquidity'

    class EthereumTxType(models.IntegerChoices):
        LEGACY = 0, 'legacy'
        EIP2930 = 1, 'EIP-2930'
        EIP1559 = 2, 'EIP-1559'

    tx_hash = models.CharField(
        max_length=66,
        primary_key=True,
        verbose_name='Transaction Hash',
    )
    chain_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Chain ID',
    )
    tx_type = models.CharField(
        null=True,
        blank=True,
        choices=TransactionType.choices,
        max_length=20,
        verbose_name='Transaction Type',
    )
    ethereum_tx_type = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=EthereumTxType.choices,
        verbose_name='Ethereum Transaction Type',
    )
    status = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='Status',
    )
    wallet_address = models.CharField(
        null=True,
        blank=True,
        max_length=42,
        verbose_name='Wallet Address',
    )
    nonce = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='Nonce',
    )
    block_number = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='Block Number',
    )
    gas_used = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='Gas Used',
    )
    gas_used_for_l1 = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='Gas Used For L1',
    )
    effective_gas_price = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='Effective Gas Price',
    )
    total_gas_cost_wei = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='Total Gas Cost WEI',
    )
    total_gas_cost_eth = models.DecimalField(
        null=True,
        blank=True,
        max_digits=30,
        decimal_places=18,
        verbose_name='Total Gas Cost ETH',
    )
    total_gas_cost_usdc = models.DecimalField(
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        verbose_name='Total Gas Cost USDC',
    )
    native_token_price_usdc = models.DecimalField(
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        verbose_name='Native Token Price USDC',
        help_text='Snapshot at moment.',
    )
    gas_limit = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='Gas Limit',
    )
    max_fee_per_gas = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='Max Fee per Gas',
    )
    max_priority_fee_per_gas = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='Max Priority Fee per Gas',
    )
    gas_price = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='Gas Price',
        help_text='Only legacy transactions are supported.',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
    )

    class Meta:
        verbose_name = 'Blockchain Transaction'
        verbose_name_plural = 'Blockchain Transaction'

    def __str__(self):
        return self.tx_hash

