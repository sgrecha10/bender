from django.contrib import admin
from django.urls import path

from core.utils.admin_utils import redirect_to_change_list
from .models import UniswapPool, Transaction, SwapChain, ERC20Token
from django.utils.safestring import mark_safe
from .tasks import (
    task_get_uniswap_pools_v3,
    task_get_uniswap_pools_v2,
    task_get_tokens_from_uniswap_pool,
)


@admin.register(UniswapPool)
class UniswapPoolAdmin(admin.ModelAdmin):
    change_list_template = 'admin/defi/uniswap_pool/change_list.html'
    list_filter = ('pool_type',)
    list_display = (
        'pool_address',
        'pool_type',
        'token_0_address',
        'token_1_address',
        'fee',
        'tick_spacing',
        'removed',
        'updated',
        'created',
    )
    readonly_fields = (
        'pool_type',
        'pool_address',
        'token_0_address',
        'token_1_address',
        'fee',
        'tick_spacing',
        'block_hash',
        'block_number',
        'block_timestamp',
        'transaction_hash',
        'transaction_index',
        'log_index',
        'removed',
        'updated',
        'created',
    )
    fieldsets = [
        ('Main', {
            'fields': [
                'pool_address',
                'pool_type',
                'token_0_address',
                'token_1_address',
                'fee',
                'tick_spacing',
                'removed',

            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('BlockChain', {
            'fields': [
                'block_hash',
                'block_number',
                'block_timestamp',
                'transaction_hash',
                'transaction_index',
                'log_index',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Information', {
            'fields': [
                'updated',
                'created',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
    ]

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path(
                'get_uniswap_pools/',
                self.admin_site.admin_view(self.get_uniswap_pools),
                name='get_uniswap_pools',
            ),
            path(
                'delete_uniswap_pools/',
                self.admin_site.admin_view(self.delete_uniswap_pools),
                name='delete_uniswap_pools',
            ),
        ]
        return added_urls + urls

    def get_uniswap_pools(self, request, *args, **kwargs):
        task_get_uniswap_pools_v2.delay()
        task_get_uniswap_pools_v3.delay()
        message = mark_safe('Таска запущена. <a href="http://localhost:5555" target="_blank">Flower</a>')
        return redirect_to_change_list(request, self.model, message)

    def delete_uniswap_pools(self, request, *args, **kwargs):
        UniswapPool.objects.all().delete()
        message = 'UniswapPool table is cleared.'
        return redirect_to_change_list(request, self.model, message)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    ordering = ('-created',)
    list_filter = ('type',)
    search_fields = ('tx_hash',)
    list_display = (
        'tx_hash',
        'type',
        'updated',
        'created',
    )
    readonly_fields = (
        'tx_hash',
        'block_hash',
        'block_number',
        'from_address',
        'to_address',
        'value',
        'gas',
        'input',
        'nonce',
        'tx_index',
        'gas_price',
        'max_fee_per_gas',
        'max_priority_fee_per_gas',
        'type',
        'chain_id',
        'y_parity',
        'access_list',
    )
    fieldsets = [
        ('Common', {
            'fields': [
                'tx_hash',
                'block_hash',
                'block_number',
                'tx_index',
                'from_address',
                'to_address',
                'value',
                'gas',
                'input',
                'nonce',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Комиссии', {
            'fields': [
                'gas_price',
                'max_fee_per_gas',
                'max_priority_fee_per_gas',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
        ('Подпись и тип', {
            'fields': [
                'type',
                'chain_id',
                'y_parity',
                'access_list',
            ],
            'classes': ('grp-collapse', 'grp-open'),
        }),
    ]


@admin.register(SwapChain)
class SwapChainAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'codename',
        'name',
        'pool_0',
        'pool_1',
        'updated',
        'created',
    )
    raw_id_fields = (
        'pool_0',
        'pool_1'
    )
    readonly_fields = (
        'updated',
        'created',
    )


@admin.register(ERC20Token)
class ERC20TokenAdmin(admin.ModelAdmin):
    change_list_template = 'admin/defi/erc20_token/change_list.html'
    list_display = (
        'address',
        'name',
        'symbol',
        'decimals',
        'total_supply',
        # 'owner',
        'version',
        # 'domain_separator',
        'updated',
        'created',
    )

    readonly_fields = (
        'address',
        'name',
        'symbol',
        'decimals',
        'total_supply',
        'owner',
        'version',
        'domain_separator',
        'server_time',
        'updated',
        'created',
    )

    def get_urls(self):
        urls = super().get_urls()
        added_urls = [
            path(
                'get_tokens_from_uniswap_pool/',
                self.admin_site.admin_view(self.get_tokens_from_uniswap_pool),
                name='get_tokens_from_uniswap_pool',
            ),
        ]
        return added_urls + urls

    def get_tokens_from_uniswap_pool(self, request, *args, **kwargs):
        """Таска загружает информацию по токенам из пулов UniswapPool"""
        task_get_tokens_from_uniswap_pool.delay()
        message = mark_safe('Таска запущена. <a href="http://localhost:5555" target="_blank">Flower</a>')
        return redirect_to_change_list(request, self.model, message)
