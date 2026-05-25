from django.contrib import admin

from .models import BlockchainTransaction


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
