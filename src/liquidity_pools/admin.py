from django.contrib import admin

from .models import BlockchainTransaction, ERC20Token
from core.utils.admin_utils import redirect_to_change_list


@admin.register(BlockchainTransaction)
class BlockchainTransactionAdmin(admin.ModelAdmin):
    list_display = (
        # 'tx_hash',
        'short_tx_hash',
        'chain_id',
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
        'chain_id',
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
                'chain_id',
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
        'chain_id',
        'name',
        'symbol',
        'decimals',
        'total_supply',
        'owner',
        'version',
        'domain_separator',
        'created_at',
    )

    readonly_fields = (
        'chain_id',
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

    @admin.action(description='Обновить')
    def update_erc20token(self, request, queryset):

        for row in queryset:
            address = row.address



        print('grecha')
        result = 123
        is_ok = True
        message = f'Обновили {result} записей' if is_ok else result
        return redirect_to_change_list(request, self.model, message, is_ok)
