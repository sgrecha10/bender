from django.contrib import admin
from .models import UniswapPool


@admin.register(UniswapPool)
class UniswapPoolAdmin(admin.ModelAdmin):
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
