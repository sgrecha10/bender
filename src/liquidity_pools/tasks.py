from decimal import Decimal

from django.utils import timezone
from web3.exceptions import TransactionNotFound
from web3.types import HexBytes, HexStr, Hash32

from bender.celery_entry import app
from core.utils.value_utils import rpc_hex_to_int
from liquidity_pools.containers.arbitrum import ArbitrumContainer
from liquidity_pools.services.w3_service import W3Service
from .interfaces import arbitrum
from .services.token_metadata_service import TokenMetadataService


@app.task(
    bind=True,
    autoretry_for=(
        TransactionNotFound,
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


@app.task(bind=True)
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


@app.task(bind=True)
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


@app.task(bind=True)
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
