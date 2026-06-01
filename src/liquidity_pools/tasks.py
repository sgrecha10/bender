from datetime import datetime
from decimal import Decimal

from django.contrib.gis.db.backends.postgis.pgraster import chunk
from django.utils import timezone
from web3.exceptions import TransactionNotFound
from web3.types import HexBytes, HexStr, Hash32

from bender.celery_entry import app
from core.utils.value_utils import rpc_hex_to_int
from liquidity_pools.containers.arbitrum import ArbitrumContainer
from liquidity_pools.services.w3_service import W3Service
from .interfaces import arbitrum
from .services.token_metadata_service import TokenMetadataService
from .services.liquidity_pool_metadata_service import LiquidityPoolMetadataService
from .services.pool_history_service import PoolHistoryLoaderService, PoolHistoryService
from requests.exceptions import ConnectionError
from http.client import RemoteDisconnected
import time



@app.task(
    bind=True,
    autoretry_for=(
        TransactionNotFound,
        ConnectionError,
        RemoteDisconnected,
    ),
    retry_kwargs={'max_retries': 10, 'countdown': 1},
)
def index_blockchain_transaction_task(
    self,
    chain_id: int,
    tx_hash: Hash32 | HexBytes | HexStr,
    tx_type: str,
):
    """Logging to BlockchainTransaction.

    :param chain_id:
    :param self:
    :param tx_hash:
    :param tx_type:
    :param created_at:
    """
    from .models import BlockchainTransaction

    w3 = W3Service(chain_id=chain_id)

    tx = w3.eth.get_transaction(transaction_hash=tx_hash)
    receipt = w3.eth.wait_for_transaction_receipt(transaction_hash=tx_hash)

    native_token_price_usdc = 2137.5  # из какого то хранилища, где оно обновляется.

    gas_used = receipt["gasUsed"]
    effective_gas_price = receipt["effectiveGasPrice"]
    total_gas_cost_wei = gas_used * effective_gas_price
    total_gas_cost_eth = Decimal(total_gas_cost_wei)  / Decimal(10 ** 18)
    total_gas_cost_usdc = Decimal(total_gas_cost_eth) * Decimal(native_token_price_usdc)

    blockchain_transaction, _ = BlockchainTransaction.objects.update_or_create(
        tx_hash=tx["hash"].hex(),
        defaults={
            'chain_id': tx["chainId"],
            'tx_type': tx_type,
            'ethereum_tx_type': receipt["type"],
            'status': bool(receipt["status"]),
            'wallet_address': tx["from"],
            'nonce': tx["nonce"],
            'block_number': receipt["blockNumber"],
            'gas_used': gas_used,
            'gas_used_for_l1': rpc_hex_to_int(receipt["gasUsedForL1"]),
            'effective_gas_price': effective_gas_price,
            'total_gas_cost_wei': total_gas_cost_wei,
            'total_gas_cost_eth': total_gas_cost_eth,
            'total_gas_cost_usdc': total_gas_cost_usdc,
            'native_token_price_usdc': native_token_price_usdc,
            'gas_limit': tx["gas"],
            'max_fee_per_gas': tx.get('maxFeePerGas'),
            'max_priority_fee_per_gas': tx.get('maxPriorityFeePerGas'),
            'gas_price': tx["gasPrice"],
        }
    )

    return blockchain_transaction.tx_hash


@app.task(
    bind=True,
    autoretry_for=(
        ConnectionError,
        RemoteDisconnected,
    ),
    retry_kwargs={'max_retries': 10, 'countdown': 1},
)
def update_token_metadata_task(
    self,
    chain_id: int,
    token_address: str,
):
    """Retrieve and update token metadata."""
    from liquidity_pools.models import ERC20Token

    w3 = W3Service(chain_id=chain_id)

    service = TokenMetadataService(
        w3=w3,
        erc20_abi=arbitrum.ERC20_ABI,
    )

    token_metadata = service.get_token_metadata(token_address=token_address)

    ERC20Token.objects.filter(pk=token_address).update(**token_metadata)

    return token_metadata


@app.task(
    bind=True,
    autoretry_for=(
        ConnectionError,
        RemoteDisconnected,
    ),
    retry_kwargs={'max_retries': 10, 'countdown': 1},
)
def update_liquidity_pool_task(
    self,
    chain_id: int,
    pool_address: str,
):
    """Retrieve and update token metadata."""
    from liquidity_pools.models import LiquidityPool

    w3 = W3Service(chain_id=chain_id)

    service = LiquidityPoolMetadataService(
        w3=w3,
        slot0_abi=arbitrum.SLOT0_ABI,
    )

    pool_metadata = service.get_liquidity_pool_metadata(pool_address=pool_address)

    LiquidityPool.objects.filter(pk=pool_address).update(**pool_metadata)

    return pool_metadata


@app.task(
    bind=True,
    autoretry_for=(
        ConnectionError,
        RemoteDisconnected,
    ),
    retry_kwargs={'max_retries': 10, 'countdown': 1},
)
def execute_swap_request_task(self, swap_request_id: int):
    """Send SwapRequest to blockchain."""

    from liquidity_pools.models import SwapRequest

    swap_request = SwapRequest.objects.get(pk=swap_request_id)
    swap_request.status = SwapRequest.Status.PROCESSING
    swap_request.save(update_fields=['status', 'updated_at'])

    try:
        container = ArbitrumContainer(
            wallet_address_id=swap_request.wallet_address_id,
        )
        container.swap_service.swap(
            swap_request_id=swap_request_id,
            amount_in=int(swap_request.amount_in),
            slippage=swap_request.slippage_percent,
            token_in=swap_request.token_in.address,
            token_out=swap_request.token_out.address,
            pool_fee=swap_request.fee,
            deadline_seconds=swap_request.deadline_seconds,
        )
        swap_request.status = SwapRequest.Status.SUCCESS
        swap_request.executed_at = timezone.now()
    except Exception as e:
        swap_request.status = SwapRequest.Status.FAILED
        # import traceback
        swap_request.error_message = (
            # str(e) + '\n' + traceback.format_exc()
            str(e)
        )

    swap_request.save(update_fields=[
        'status',
        'error_message',
        'executed_at',
        'updated_at',
    ])


@app.task(
    bind=True,
    autoretry_for=(
        ConnectionError,
        RemoteDisconnected,
    ),
    retry_kwargs={'max_retries': 10, 'countdown': 1},
)
def execute_liquidity_removal_request(self, liquidity_removal_request_id: int):
    """Send LiquidityRemovalRequest to blockchain."""

    from liquidity_pools.models import LiquidityRemovalRequest

    liquidity_removal_request = LiquidityRemovalRequest.objects.get(pk=liquidity_removal_request_id)
    liquidity_removal_request.status = LiquidityRemovalRequest.Status.PROCESSING
    liquidity_removal_request.save(update_fields=['status', 'updated_at'])

    try:
        container = ArbitrumContainer(
            wallet_address_id=liquidity_removal_request.wallet_address_id,
        )
        container.liquidity_removal_service.remove_liquidity(
            liquidity_removal_request_id=liquidity_removal_request_id,
            token_id=liquidity_removal_request.pool_token_id,
            removal_percentage=liquidity_removal_request.removal_percentage,
            deadline_seconds=liquidity_removal_request.deadline_seconds,
        )
        liquidity_removal_request.status = LiquidityRemovalRequest.Status.SUCCESS
        liquidity_removal_request.executed_at = timezone.now()
    except Exception as e:
        liquidity_removal_request.status = LiquidityRemovalRequest.Status.FAILED
        # import traceback
        liquidity_removal_request.error_message = (
            # str(e) + '\n' + traceback.format_exc()
            str(e)
        )

    liquidity_removal_request.save(update_fields=[
        'status',
        'error_message',
        'executed_at',
        'updated_at',
    ])


@app.task(
    bind=True,
    autoretry_for=(
        ConnectionError,
        RemoteDisconnected,
    ),
    retry_kwargs={'max_retries': 10, 'countdown': 1},
)
def execute_liquidity_mint_request(self, liquidity_mint_request_id: int):
    """Send LiquidityMintRequest to blockchain."""

    from liquidity_pools.models import LiquidityMintRequest

    liquidity_mint_request = LiquidityMintRequest.objects.get(pk=liquidity_mint_request_id)
    liquidity_mint_request.status = LiquidityMintRequest.Status.PROCESSING
    liquidity_mint_request.save(update_fields=['status', 'updated_at'])

    try:
        container = ArbitrumContainer(
            wallet_address_id=liquidity_mint_request.wallet_address_id,
        )
        container.liquidity_mint_service.mint_liquidity(
            liquidity_mint_request_id=liquidity_mint_request_id,
            liquidity_pool=liquidity_mint_request.liquidity_pool,
            amount0_desired=int(liquidity_mint_request.amount0_desired),
            amount1_desired=int(liquidity_mint_request.amount1_desired),
            range_upper_price=liquidity_mint_request.range_upper_price,
            range_lower_price=liquidity_mint_request.range_lower_price,
            amount0_min=int(liquidity_mint_request.amount0_min),
            amount1_min=int(liquidity_mint_request.amount1_min),
            slippage_percent=liquidity_mint_request.slippage_percent,
            deadline_seconds=liquidity_mint_request.deadline_seconds,
        )
        liquidity_mint_request.status = LiquidityMintRequest.Status.SUCCESS
        liquidity_mint_request.executed_at = timezone.now()
    except Exception as e:
        liquidity_mint_request.status = LiquidityMintRequest.Status.FAILED
        import traceback
        liquidity_mint_request.error_message = (
            str(e) + '\n' + traceback.format_exc()
            # str(e)
        )

    liquidity_mint_request.save(update_fields=[
        'status',
        'error_message',
        'executed_at',
        'updated_at',
    ])


@app.task(bind=True)
def get_pool_historical_block_ticks(self, liquidity_pool_address: str):
    from liquidity_pools.models import LiquidityPool, LiquidityPoolTick

    liquidity_pool = LiquidityPool.objects.get(pk=liquidity_pool_address)

    w3 = W3Service(chain_id=liquidity_pool.chain_id)

    service = PoolHistoryService(
        w3=w3,
        pool_address=liquidity_pool.address,
        slot0=arbitrum.SLOT0_ABI,
    )

    # =================================================
    start_date = datetime(year=2026, month=5, day=27, hour=0, minute=0, second=0)
    end_date = datetime(year=2026, month=5, day=29, hour=0, minute=0, second=0)

    interval = 60  # minutes
    chunk_size = 10 # количество запросов до паузы
    delay = 0.5  # задержка между чанками, сек.
    # =================================================

    start_block_number = service.find_block_by_timestamp(
        target_timestamp=int(start_date.timestamp()),
    )
    end_block_number = service.find_block_by_timestamp(
        target_timestamp=int(end_date.timestamp()),
    )

    # start_block_number = 467_372_633
    # end_block_number = 467_717_657

    step = int(interval * 60 / liquidity_pool.chain.block_time)
    chunk_size = chunk_size * step

    while start_block_number < end_block_number:
        finish_block_number = start_block_number + chunk_size
        if finish_block_number > end_block_number:
            finish_block_number= end_block_number

        rows = []
        for block_number in range(
            start_block_number,
            finish_block_number,
            step
        ):
            print('for - block_number', block_number)
            tick = service.get_tick(block_number=block_number)
            block_timestamp = service.get_block_datetime(block_number=block_number)
            rows.append({
                'block_number': block_number,
                'tick': tick,
                'block_timestamp': block_timestamp,
            })

        LiquidityPoolTick.objects.bulk_create(
            [
                LiquidityPoolTick(
                    liquidity_pool_id=liquidity_pool.address,
                    block_number=row['block_number'],
                    tick=row['tick'],
                    block_timestamp=row['block_timestamp'],
                )
                for row in rows
            ],
            ignore_conflicts=True,
        )

        start_block_number = finish_block_number
        print('while - start_block_number', start_block_number)
        time.sleep(delay)









# @app.task(
#     bind=True,
#     autoretry_for=(
#         ConnectionError,
#         RemoteDisconnected,
#     ),
#     retry_kwargs={'max_retries': 10, 'countdown': 1},
# )
# def get_pool_historical_ticks(self, liquidity_pool_address: str):
#     """Не используем."""
#     from liquidity_pools.models import LiquidityPool, LiquidityPoolTick
#
#     # =================================================
#     start_date = datetime(year=2026, month=5, day=28, hour=0, minute=0, second=0)
#     end_date = datetime(year=2026, month=5, day=29, hour=0, minute=0, second=0)
#     chunk_size = 128
#     # =================================================
#
#     liquidity_pool = LiquidityPool.objects.get(pk=liquidity_pool_address)
#
#     w3 = W3Service(chain_id=liquidity_pool.chain_id)
#
#     service = PoolHistoryLoaderService(
#         w3=w3,
#         pool_address=liquidity_pool.address,
#         pool_abi=arbitrum.POOL_ABI,
#     )
#
#     start_block_number = service.find_block_by_timestamp(
#         target_timestamp=int(start_date.timestamp()),
#     )
#     # start_block_number = 12_000
#
#     end_block_number = service.find_block_by_timestamp(
#         target_timestamp=int(end_date.timestamp()),
#     )
#     # end_block_number = start_block_number + 1000
#
#     print('Calculated block numbers.')
#     print('start_block_number:', start_block_number)
#     print('end_block_number:', end_block_number)
#
#     while start_block_number < end_block_number:
#         rows = service.load(
#             from_block=start_block_number,
#             to_block=start_block_number + chunk_size,
#         )
#
#         LiquidityPoolTick.objects.bulk_create(
#             [
#                 LiquidityPoolTick(
#                     liquidity_pool_id=liquidity_pool.address,
#                     block_number=row['block_number'],
#                     tick=row['tick'],
#                     liquidity=row['liquidity'],
#                     block_timestamp=row['block_timestamp'],
#                 )
#                 for row in rows
#             ],
#             ignore_conflicts=True,
#         )
#
#         start_block_number += chunk_size
#         print('start_block_number:', start_block_number)
#         time.sleep(0.5)
