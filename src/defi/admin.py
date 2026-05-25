from django.contrib import admin
from django.contrib import messages
from django.urls import path
from django.urls import reverse
from django.utils.safestring import mark_safe

from core.utils.admin_utils import redirect_to_change_list, redirect_to_change_form
from defi.tasks import task_get_erc20_eip2612
from .models import (
    UniswapPool,
    Transaction,
    SwapChain,
    ERC20Token,
    PoolLiquidity,
)
from .tasks import (
    task_get_uniswap_pools_v3,
    task_get_uniswap_pools_v2,
    task_get_tokens_from_uniswap_pool,
)


@admin.register(UniswapPool)
class UniswapPoolAdmin(admin.ModelAdmin):
    change_list_template = 'admin/defi/uniswap_pool/change_list.html'
    list_filter = ('pool_type',)
    search_fields = (
        'pool_address',
        'token_0_address',
        'token_1_address',
    )
    list_display = (
        'pool_address',
        'pool_type',
        'token_0_address',
        'display_token_0_symbol',
        'token_1_address',
        'display_token_1_symbol',
        'fee',
        'tick_spacing',
        'removed',
        # 'updated',
        # 'created',
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
        'display_token_0',
        'display_token_1',
        'display_token_0_symbol',
        'display_token_1_symbol',
    )
    fieldsets = [
        ('Main', {
            'fields': [
                'pool_address',
                'pool_type',
                # 'token_0_address',
                'display_token_0',
                # 'token_1_address',
                'display_token_1',
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

    def _display_token_symbol(self, obj, token_address):
        try:
            erc20_token = ERC20Token.objects.get(address=token_address)
            return erc20_token.symbol
        except ERC20Token.DoesNotExist:
            return

    @admin.display(description='Token 0 Symbol')
    def display_token_0_symbol(self, obj):
        token_address = obj.token_0_address
        return self._display_token_symbol(obj, token_address)

    @admin.display(description='Token 1 Symbol')
    def display_token_1_symbol(self, obj):
        token_address = obj.token_1_address
        return self._display_token_symbol(obj, token_address)

    def _display_token(self, obj, token_address: str):
        try:
            erc20_token = ERC20Token.objects.get(address=token_address)
        except ERC20Token.DoesNotExist:
            erc20_token = None

        if erc20_token:
            meta = ERC20Token._meta
            url = reverse(
                f'admin:{meta.app_label}_{meta.model_name}_change',
                args=(token_address,)
            )
            return mark_safe(
                '<a href="{}" target="_blank">{}</a> | {} | {}'.format(
                    url,
                    token_address,
                    erc20_token.name,
                    erc20_token.symbol,
                )
            )

        return mark_safe(
            '{} | <a href="{}?token_address={}">Get token data</a>'.format(
                token_address,
                reverse('admin:get_token_data', args=(obj.pk,)),
                token_address,
            )
        )

    @admin.display(description='Token 0')
    def display_token_0(self, obj):
        token_address = obj.token_0_address
        return self._display_token(obj, token_address)

    @admin.display(description='Token 1')
    def display_token_1(self, obj):
        token_address = obj.token_1_address
        return self._display_token(obj, token_address)

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
            path(
                '<pk>/get_token_data/',
                self.admin_site.admin_view(self.get_token_data),
                name='get_token_data',
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

    def get_token_data(self, request, *args, **kwargs):
        token_address = request.GET['token_address']
        task_get_erc20_eip2612.delay(token_address=token_address)
        messages.success(request, 'task_get_erc20_eip2612 started..')
        return redirect_to_change_form(self.model, kwargs['pk'])


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
        'is_active',
        # 'pool_0',
        'display_pool_0',
        # 'pool_1',
        'display_pool_1',
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
        'display_pool_0',
        'display_pool_1',
    )

    @admin.display(description='Pool 0')
    def display_pool_0(self, obj):
        return self._display_pool(pool=obj.pool_0)

    @admin.display(description='Pool 1')
    def display_pool_1(self, obj):
        return self._display_pool(pool=obj.pool_1)

    def _display_pool(self, pool: UniswapPool):
        meta = ERC20Token._meta
        token_address_0 = pool.token_0_address
        token_address_1 = pool.token_1_address

        url_0 = reverse(
            f'admin:{meta.app_label}_{meta.model_name}_change',
            args=(token_address_0,)
        )
        url_1 = reverse(
            f'admin:{meta.app_label}_{meta.model_name}_change',
            args=(token_address_1,)
        )

        return mark_safe(
            '{}<br>'
            '<a href="{}" target="_blank">{}</a><br>'
            '<a href="{}" target="_blank">{}</a><br>'.format(
                pool,
                url_0, token_address_0,
                url_1, token_address_1,
            )
        )


@admin.register(ERC20Token)
class ERC20TokenAdmin(admin.ModelAdmin):
    change_list_template = 'admin/defi/erc20_token/change_list.html'
    search_fields = ('address', 'symbol')
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


@admin.register(PoolLiquidity)
class PoolLiquidityAdmin(admin.ModelAdmin):
    list_display = (
        # 'id',
        'pool',
        'reserve0',
        'reserve1',
        'updated',
        'created',
    )

    readonly_fields = list_display + ('server_time',)
