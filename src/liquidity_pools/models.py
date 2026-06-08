from django.conf import settings
from django.db import models
from django.db.models import Sum

from liquidity_pools.constants import Interval


class Chain(models.Model):
    id = models.PositiveIntegerField(
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
        return f'{self.name} ({self.id})'


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
    chain = models.ForeignKey(
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
        return f'{self.label} |  {self.address[:6]}...{self.address[-4:]} | {self.chain}'


class ERC20Token(models.Model):
    address = models.CharField(
        primary_key=True,
        max_length=42,
        verbose_name='Address',
    )
    chain = models.ForeignKey(
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
        # return (
        #     f'{self.symbol} ({self.chain.name})'
        # )


class LiquidityPool(models.Model):
    address = models.CharField(
        primary_key=True,
        max_length=42,
        verbose_name='Pool Address',
    )
    chain = models.ForeignKey(
        Chain,
        on_delete=models.CASCADE,
        verbose_name='Chain',
    )
    token0 = models.ForeignKey(
        ERC20Token,
        on_delete=models.CASCADE,
        null=True,
        related_name='token0_pools',
        verbose_name='Token0',
    )
    token1 = models.ForeignKey(
        ERC20Token,
        on_delete=models.CASCADE,
        null=True,
        related_name='token1_pools',
        verbose_name='Token1',
    )
    fee = models.PositiveIntegerField(
        null=True,
        verbose_name='Fee',
        help_text='100, 500, 3000, 10000',
    )
    tick_spacing = models.PositiveIntegerField(
        null=True,
        verbose_name='Tick Spacing',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
    )

    class Meta:
        verbose_name = 'Liquidity Pool'
        verbose_name_plural = 'Liquidity Pools'

    def __str__(self):
        return (
            f'{self.token0.symbol} '
            f'/ {self.token1.symbol} '
            f'- {self.fee / 10000}% '
            f'| {self.address[:6]}...{self.address[-4:]}'
        )

class BlockchainTransaction(models.Model):
    """Logging."""

    class TransactionType(models.TextChoices):
        SWAP = 'swap', 'Swap'
        MINT = 'mint', 'Mint'
        BURN = 'burn', 'Burn'
        COLLECT = 'collect', 'Collect'
        APPROVE = 'approve', 'Approve'
        DECREASE_LIQUIDITY = 'decrease_liquidity', 'Decrease Liquidity'
        UNKNOWN = 'unknown', 'Unknown'

    class EthereumTxType(models.IntegerChoices):
        LEGACY = 0, 'legacy'
        EIP2930 = 1, 'EIP-2930'
        EIP1559 = 2, 'EIP-1559'

    tx_hash = models.CharField(
        max_length=66,
        primary_key=True,
        verbose_name='Transaction Hash',
    )
    chain = models.ForeignKey(
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


class LiquidityRemovalRequest(models.Model):
    """Liquidity removal request."""

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
    pool_token_id = models.PositiveBigIntegerField(
        verbose_name='Pool Token ID',
    )
    removal_percentage = models.PositiveSmallIntegerField(
        default=100,
        verbose_name='Removal Percentage',
    )
    deadline_seconds = models.PositiveIntegerField(
        default=600,
        verbose_name='Deadline Seconds',
    )
    blockchain_transaction = models.ManyToManyField(
        BlockchainTransaction,
        through='LiquidityRemovalRequestTransaction',
        related_name='liquidity_removal_request',
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
        verbose_name = 'Liquidity Removal Request'
        verbose_name_plural = 'Liquidity Removal Requests'

    def __str__(self):
        return (
            f'{self.pool_token_id} | {self.removal_percentage}'
        )

    @property
    def gas_used_total(self):
        return self.blockchain_transaction.aggregate(sum=Sum('gas_used'))['sum']

    @property
    def gas_cost_usdc_total(self):
        return self.blockchain_transaction.aggregate(sum=Sum('total_gas_cost_usdc'))['sum']


class LiquidityRemovalRequestTransaction(models.Model):
    """M2M table for relation."""
    liquidity_removal_request = models.ForeignKey(
        LiquidityRemovalRequest,
        on_delete=models.CASCADE,
    )
    blockchain_transaction = models.OneToOneField(
        BlockchainTransaction,
        on_delete=models.CASCADE,
        unique=True,
    )


class LiquidityMintRequest(models.Model):
    """Liquidity mint request."""

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
    liquidity_pool = models.ForeignKey(
        LiquidityPool,
        on_delete=models.CASCADE,
        verbose_name='Liquidity Pool',
    )
    amount0_desired = models.DecimalField(
        max_digits=78,
        decimal_places=0,
        verbose_name='Amount0 Desired',
    )
    amount1_desired = models.DecimalField(
        max_digits=78,
        decimal_places=0,
        verbose_name='Amount1 Desired',
    )
    range_upper_price = models.DecimalField(
        max_digits=78,
        decimal_places=5,
        verbose_name='Range Upper Price',
        help_text='Price in Token1',
    )
    range_lower_price = models.DecimalField(
        max_digits=78,
        decimal_places=5,
        verbose_name='Range Lower Price',
        help_text='Price in Token1',
    )
    amount0_min = models.DecimalField(
        max_digits=78,
        decimal_places=0,
        default=0,
        verbose_name='Amount0 Min',
    )
    amount1_min = models.DecimalField(
        max_digits=78,
        decimal_places=0,
        default=0,
        verbose_name='Amount1 Min',
    )
    slippage_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.50,
        verbose_name='Slippage Percent',
        help_text=(
            'Не использую. Но можно прикрутить так: выбирать меньшее значение из amount0_desired/amount1_desired,'
            ' применяешь значение из этого поля и заполняешь соответствующее поле amount0_min/amount1_min. '
            'Во втором поле amount_min ставим 0. Получается страховка от ситуации, когда цена сильно уехала после '
            'отпарвки транзакции. Не уверен что это нужно сейчас.'
        ),
    )

    deadline_seconds = models.PositiveIntegerField(
        default=600,
        verbose_name='Deadline Seconds',
    )
    blockchain_transaction = models.ManyToManyField(
        BlockchainTransaction,
        through='LiquidityMintRequestTransaction',
        related_name='liquidity_mint_request',
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
        verbose_name = 'Liquidity Mint Request'
        verbose_name_plural = 'Liquidity Mint Requests'

    def __str__(self):
        return (
            f'Mint | {self.liquidity_pool} '
        )

    @property
    def gas_used_total(self):
        return self.blockchain_transaction.aggregate(sum=Sum('gas_used'))['sum']

    @property
    def gas_cost_usdc_total(self):
        return self.blockchain_transaction.aggregate(sum=Sum('total_gas_cost_usdc'))['sum']


class LiquidityMintRequestTransaction(models.Model):
    """M2M table for relation."""
    liquidity_mint_request = models.ForeignKey(
        LiquidityMintRequest,
        on_delete=models.CASCADE,
    )
    blockchain_transaction = models.OneToOneField(
        BlockchainTransaction,
        on_delete=models.CASCADE,
        unique=True,
    )


class LiquidityPoolTick(models.Model):
    liquidity_pool = models.ForeignKey(
        LiquidityPool,
        on_delete=models.CASCADE,
    )
    block_number = models.BigIntegerField(
        blank=True,
        null=True,
        verbose_name='Block Number',
    )
    tick = models.IntegerField(
        verbose_name='Tick',
    )
    liquidity =models.PositiveBigIntegerField(
        blank=True,
        null=True,
        verbose_name='Liquidity',
    )
    block_timestamp = models.DateTimeField(
        verbose_name='Block Timestamp',
    )

    class Meta:
        verbose_name = 'Liquidity Pool Tick'
        verbose_name_plural = 'Liquidity Pool Ticks'
        indexes = [
            models.Index(
                fields=('liquidity_pool', 'block_timestamp'),
            ),
        ]

    def __str__(self):
        return f'Liquidity Pool Tick | {self.id}'


class Strategy(models.Model):

    class StdSource(models.TextChoices):
        CLOSE_TO_CLOSE = 'close_to_close', 'Realized volatility'
        PARKINSON = 'parkinson', 'Parkinson volatility'

    class EnteringTradeCondition(models.TextChoices):
        OPEN_PRICE = 'open_price', 'Candle open price'

    class IntrabarPricePath(models.TextChoices):
        OHLC = 'ohlc', 'Better, high first'
        OLHC = 'olhc', 'Worse, low first'

    name = models.CharField(
        max_length=255,
        verbose_name='Name',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description',
    )
    liquidity_pool = models.ForeignKey(
        LiquidityPool,
        on_delete=models.CASCADE,
        verbose_name='Liquidity Pool',
    )
    interval = models.CharField(
        max_length=50,
        choices=Interval.choices,
        default=Interval.DAY_1,
        verbose_name='Interval',
    )
    std_window_size = models.PositiveIntegerField(
        default=7,
        verbose_name='Window Size',
    )
    std_source = models.CharField(
        max_length=50,
        choices=StdSource.choices,
        default=StdSource.CLOSE_TO_CLOSE,
        verbose_name='Source',
    )
    z_score_upper = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        verbose_name='Z-Score Upper',
    )
    z_score_lower = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        verbose_name='Z-Score Lower',
    )
    time_horizon = models.CharField(
        max_length=50,
        choices=Interval.choices,
        default=Interval.DAY_1,
        verbose_name='Time Horizon',
    )
    entering_trade_condition = models.CharField(
        max_length=50,
        choices=EnteringTradeCondition.choices,
        default=EnteringTradeCondition.OPEN_PRICE,
        verbose_name='Entering Trade Condition',
    )
    maximum_range_width = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Maximum Range Width',
    )
    intrabar_price_path = models.CharField(
        max_length=50,
        choices=IntrabarPricePath.choices,
        default=IntrabarPricePath.OHLC,
        verbose_name='Intrabar Price Path',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
    )

    class Meta:
        verbose_name = 'Strategy'
        verbose_name_plural = 'Strategies'

    def __str__(self):
        return (
            f'{self.pk} | {self.name} '
        )


class StrategyPosition(models.Model):

    class StatusChoice(models.TextChoices):
        OPEN = 'open', 'Open'
        CLOSED_BY_RANGE = 'closed_by_range', 'Closed by range'
        CLOSED_FOR_REBALANCING = 'closed_for_rebalancing', 'Closed for rebalancing'
        CLOSED_MANUAL = 'closed_manual', 'Closed manual'

    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE,
        verbose_name='Strategy',
    )
    opened_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Opened at',
    )
    closed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Closed at',
    )
    entry_price = models.DecimalField(
        max_digits=30,
        decimal_places=18,
        verbose_name='Entry Price',
    )
    exit_price = models.DecimalField(
        blank=True,
        null=True,
        max_digits=30,
        decimal_places=18,
        verbose_name='Exit Price',
    )
    lower_price = models.DecimalField(
        max_digits=30,
        decimal_places=18,
        verbose_name='Lower Price',
    )
    upper_price = models.DecimalField(
        max_digits=30,
        decimal_places=18,
        verbose_name='Upper Price',
    )
    status = models.CharField(
        max_length=50,
        choices=StatusChoice.choices,
        default=StatusChoice.OPEN,
        verbose_name='Status',
    )

    class Meta:
        verbose_name = 'Strategy Position'
        verbose_name_plural = 'Strategy Positions'

    def __str__(self):
        return f'{self.pk}'
