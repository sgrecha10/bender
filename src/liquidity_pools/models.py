from django.db import models
from django.conf import settings
from django.db.models import Sum


class Chain(models.Model):
    chain_id = models.PositiveIntegerField(
        primary_key=True,
        verbose_name='Chain ID',
    )
    name = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='Chain Name',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Slug',
    )
    rpc_urls = models.JSONField(
        default=list,
        verbose_name='RPC URLs',
    )
    ws_rpc_urls = models.JSONField(
        blank=True,
        null=True,
        default=list,
        verbose_name='Websocket RPC URLs',
    )
    explorer_url = models.URLField(
        blank=True,
        verbose_name='Explorer URL',
    )
    native_token_symbol = models.CharField(
        max_length=16,
        default='ETH',
        verbose_name='Native Token Symbol',
    )
    native_token_decimals = models.PositiveSmallIntegerField(
        default=18,
        verbose_name='Native Token Decimals',
    )
    block_time = models.FloatField(
        blank=True,
        null=True,
        help_text='Average block time in seconds',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At',
    )

    class Meta:
        verbose_name = 'Chain'
        verbose_name_plural = 'Chains'

    def __str__(self):
        return f'{self.name} ({self.chain_id})'


class WalletAddress(models.Model):
    address = models.CharField(
        max_length=64,
        blank=True,
        unique=True,
        db_index=True,
        verbose_name='Address',
    )
    label = models.CharField(
        blank=True,
        max_length=255,
        verbose_name='Label',
    )
    encrypted_private_key = models.JSONField(
        blank=True,
        verbose_name='Encrypted Private Key',
    )
    chain_id = models.ForeignKey(
        Chain,
        on_delete=models.CASCADE,
        verbose_name='Chain ID',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active',
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last Used At',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At',
    )

    class Meta:
        verbose_name = 'Wallet Address'
        verbose_name_plural = 'Wallet Addresses'

    def __str__(self):
        return f'{self.label} |  {self.address[:6]}...{self.address[-4:]} | {self.chain_id}'


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
    chain_id = models.ForeignKey(
        Chain,
        on_delete=models.CASCADE,
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
        verbose_name_plural = 'Blockchain Transactions'

    def __str__(self):
        return self.tx_hash


class ERC20Token(models.Model):
    address = models.CharField(
        primary_key=True,
        max_length=42,
        verbose_name='Address',
    )
    chain_id = models.ForeignKey(
        Chain,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Chain ID',
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
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
    )

    class Meta:
        verbose_name = 'ERC-20 Token'
        verbose_name_plural = 'ERC-20 Tokens'

    def __str__(self):
        return f'{self.symbol} | {self.pk[:6]}...{self.pk[-4:]}'


class SwapRequest(models.Model):
    """Swap request."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'

    wallet_address = models.ForeignKey(
        WalletAddress,
        on_delete=models.CASCADE,
        verbose_name='Wallet Address',
    )
    token_in = models.ForeignKey(
        ERC20Token,
        on_delete=models.PROTECT,
        related_name='token_in',
        verbose_name='Token In',
    )
    token_out = models.ForeignKey(
        ERC20Token,
        on_delete=models.PROTECT,
        related_name='token_out',
        verbose_name='Token Out',
    )
    amount_in = models.DecimalField(
        max_digits=78,
        decimal_places=0,
        verbose_name='Amount In',
    )
    amount_out_min = models.DecimalField(
        max_digits=78,
        decimal_places=0,
        default=0,
        verbose_name='Amount Out Min',
    )
    fee = models.PositiveIntegerField(
        default=500,
        verbose_name='Fee',
    )
    slippage_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.50,
        verbose_name='Slippage Percent',
    )
    deadline_seconds = models.PositiveIntegerField(
        default=600,
        verbose_name='Deadline Seconds',
    )
    blockchain_transaction = models.ManyToManyField(
        BlockchainTransaction,
        through='SwapRequestTransaction',
        related_name='swap_request',
        verbose_name='Blockchain Transactions',
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Status',
    )
    error_message = models.TextField(
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    executed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Swap Request'
        verbose_name_plural = 'Swap Requests'

    def __str__(self):
        return (
            f'{self.token_in} -> '
            f'{self.token_out} '
            f'({self.amount_in})'
        )

    @property
    def gas_used_total(self):
        return self.blockchain_transaction.aggregate(sum=Sum('gas_used'))['sum']

    @property
    def gas_cost_usdc_total(self):
        return self.blockchain_transaction.aggregate(sum=Sum('total_gas_cost_usdc'))['sum']


class SwapRequestTransaction(models.Model):
    """M2M table for relation."""
    swap_request = models.ForeignKey(
        SwapRequest,
        on_delete=models.CASCADE,
    )
    blockchain_transaction = models.OneToOneField(
        BlockchainTransaction,
        on_delete=models.CASCADE,
        unique=True,
    )
