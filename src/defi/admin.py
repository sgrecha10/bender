from django.contrib import admin
from django.urls import path

from core.utils.admin_utils import redirect_to_change_list
from .models import UniswapPool


@admin.register(UniswapPool)
class UniswapPoolAdmin(admin.ModelAdmin):
    change_list_template = 'admin/defi/uniswap_pool/change_list.html'
    list_display = (
        'id',
        'pool_type',
        'pool_address',
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
                # 'id',
                'pool_type',
                'pool_address',
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
        message = 'Message 1'
        return redirect_to_change_list(request, self.model, message)

    def delete_uniswap_pools(self, request, *args, **kwargs):
        UniswapPool.objects.all().delete()
        message = 'UniswapPool table is cleared.'
        return redirect_to_change_list(request, self.model, message)
