from django.contrib import admin

from core.utils.admin_utils import redirect_to_change_list
from liquidity_pools.forms import WalletAdminForm
from .models import (
    WalletAddress,
    BlockchainTransaction,
    ERC20Token,
    SwapRequest,
    Chain,
)
from .tasks import (
    update_token_metadata_task,
    execute_swap_request_task,
)


@admin.register(BlockchainTransaction)
class BlockchainTransactionAdmin(admin.ModelAdmin):
    list_display = (
        # 'tx_hash',
        'short_tx_hash',
        'chain',
        'tx_type',
        # 'ethereum_tx_type',
        'status',
        # 'wallet_address',
        'nonce',
        # 'block_number',
        'gas_used',
        # 'gas_used_for_l1',
        'effective_gas_price',
        'total_gas_cost_wei',
        'total_gas_cost_eth',
        'total_gas_cost_usdc',
        'native_token_price_usdc',
        'gas_limit',
        # 'max_fee_per_gas',
        # 'max_priority_fee_per_gas',
        'gas_price',
        'created_at',
    )
    readonly_fields = (
        'tx_hash',
        'short_tx_hash',
        'chain',
        'tx_type',
        'ethereum_tx_type',
        'status',
        'wallet_address',
        'nonce',
        'block_number',
        'gas_used',
        'gas_used_for_l1',
        'effective_gas_price',
        'total_gas_cost_wei',
        'total_gas_cost_eth',
        'total_gas_cost_usdc',
        'native_token_price_usdc',
        'gas_limit',
        'max_fee_per_gas',
        'max_priority_fee_per_gas',
        'gas_price',
        'created_at',
    )

    fieldsets = [
        ('Main', {
            'fields': [
                'tx_hash',
                'chain',
                'tx_type',
                'ethereum_tx_type',
                'status',
                'nonce',
                'block_number',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Transaction', {
            'fields': [
                'gas_limit',
                'max_fee_per_gas',
                'max_priority_fee_per_gas',
                'gas_price',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Receipt', {
            'fields': [
                'gas_used',
                'gas_used_for_l1',
                'effective_gas_price',
                'total_gas_cost_wei',
                'total_gas_cost_eth',
                'total_gas_cost_usdc',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Other', {
            'fields': [
                'native_token_price_usdc',
                'wallet_address',
                'created_at',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
    ]

    ordering = ('-created_at',)
    search_fields = ('tx_hash',)

    @admin.display(description='Transaction hash')
    def short_tx_hash(self, obj):
        return f'{obj.tx_hash[:6]}...{obj.tx_hash[-4:]}'


@admin.register(ERC20Token)
class ERC20TokenAdmin(admin.ModelAdmin):
    list_display = (
        'address',
        'chain',
        'name',
        'symbol',
        'decimals',
        'total_supply',
        'owner',
        'version',
        # 'domain_separator',
        'created_at',
    )

    readonly_fields = (
        'name',
        'symbol',
        'decimals',
        'total_supply',
        'owner',
        'version',
        'domain_separator',
        'created_at',
    )

    actions = (
        'update_erc20token',
    )

    @admin.action(description='Обновить выбранные ERC-20 Tokens')
    def update_erc20token(self, request, queryset):
        for row in queryset:
            update_token_metadata_task.delay(
                chain_id=row.chain_id,
                token_address=row.address,
            )
        count = queryset.count()
        message = f'Запущено обновление {count} токенов.'
        return redirect_to_change_list(request, self.model, message)


class BlockchainTransactionInlineAdmin(admin.TabularInline):
    classes = ('grp-collapse grp-open',)
    model = SwapRequest.blockchain_transaction.through
    extra = 0
    fields = (
        'blockchain_transaction',
        'tx_type',
        'status',
        'nonce',
        'gas_used',
        'total_gas_cost_usdc',
    )
    readonly_fields = (
        'blockchain_transaction',
        'tx_type',
        'status',
        'nonce',
        'gas_used',
        'total_gas_cost_usdc',
    )

    def has_delete_permission(self, request, obj = ...):
        return False

    def has_add_permission(self, request, obj = None):
        return False

    def tx_type(self, obj):
        return obj.blockchain_transaction.get_tx_type_display()

    @admin.display(boolean=True)
    def status(self, obj):
        return obj.blockchain_transaction.status

    def nonce(self, obj):
        return obj.blockchain_transaction.nonce

    def gas_used(self, obj):
        return obj.blockchain_transaction.gas_used

    def total_gas_cost_usdc(self, obj):
        return obj.blockchain_transaction.total_gas_cost_usdc


@admin.register(SwapRequest)
class SwapRequestAdmin(admin.ModelAdmin):
    inlines = (
        BlockchainTransactionInlineAdmin,
    )
    list_display = (
        'id',
        'wallet_address',
        'token_in',
        'token_out',
        'amount_in',
        'fee',
        'slippage_percent',
        'deadline_seconds',
        'status',
        'gas_used_total',
        'gas_cost_usdc_total',
        # 'created_by',
        # 'created_at',
        # 'updated_at',
        'executed_at',
    )
    readonly_fields = (
        'status',
        'error_message',
        'created_at',
        'updated_at',
        'executed_at',
        'gas_used_total',
        'gas_cost_usdc_total',
    )
    fieldsets = [
        (None, {
            'fields': [
                'wallet_address',
                'token_in',
                'token_out',
                'amount_in',
                'slippage_percent',
                'fee',
                'deadline_seconds',
                'created_by',
            ]
        }),
        ('Result', {
            'fields': [
                'gas_used_total',
                'gas_cost_usdc_total',
                'status',
                'error_message',
                'executed_at',
                'updated_at',
                'created_at',
            ]
        })
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            execute_swap_request_task.delay(
                swap_request_id=obj.id,
            )


@admin.register(WalletAddress)
class WalletAddressAdmin(admin.ModelAdmin):
    form = WalletAdminForm
    list_display = (
        'address',
        'label',
        'chain',
        'is_active',
        'last_used_at',
        'created_at',
        'updated_at',
    )
    readonly_fields = (
        'address',
        'encrypted_private_key',
        'last_used_at',
        'created_at',
        'updated_at',
    )

    def get_fields(self, request, obj=None):
        if obj is None:
            return (
                'private_key',
                'label',
                'chain',
                'is_active',
            )

        # редактирование
        return (
            'address',
            'label',
            'chain',
            'is_active',
            'encrypted_private_key',
            'last_used_at',
            'created_at',
            'updated_at',
        )


@admin.register(Chain)
class ChainAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ('name',)
    }
    list_display = (
        'id',
        'name',
        'slug',
        'rpc_urls',
        'ws_rpc_urls',
        'explorer_url',
        'native_token_symbol',
        'native_token_decimals',
        'block_time',
        'is_active',
        'updated_at',
        'created_at',
    )
