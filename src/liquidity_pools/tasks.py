from decimal import Decimal

from django.conf import settings
from web3 import Web3
from web3.exceptions import TransactionNotFound
from web3.types import HexBytes, HexStr, Hash32

from bender.celery_entry import app
from core.clients.blockchain.blockchain_client import BlockchainClient
from core.utils.value_utils import rpc_hex_to_int
from .services.token_metadata_service import TokenMetadataService
from .interfaces import arbitrum
from eth_account.account import Account


@app.task(
    bind=True,
    autoretry_for=(
        TransactionNotFound,
    ),
    retry_kwargs={'max_retries': 10, 'countdown': 1},
)
def index_blockchain_transaction_task(
    self,
    tx_hash: Hash32 | HexBytes | HexStr,
    tx_type: str,
):
    """Logging to BlockchainTransaction.

    :param self:
    :param tx_hash:
    :param tx_type:
    :param created_at:
    """
    from .models import BlockchainTransaction

    rpc_url = settings.RPC_DATA['arbitrum_rpc_url']
    w3 = Web3(Web3.HTTPProvider(endpoint_uri=rpc_url))

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
    token_address: str,
):
    """Retrieve and update token metadata."""
    from liquidity_pools.models import ERC20Token

    w3 = Web3(Web3.HTTPProvider(
        endpoint_uri=settings.RPC_DATA['arbitrum_rpc_url'])
    )
    account = Account.from_key(
        private_key=settings.WALLET_PRIVATE_KEYS['arbitrum_private_key']
    )

    blockchain_client = BlockchainClient(
        w3=w3,
        account=account,
    )

    service = TokenMetadataService(
        blockchain_client=blockchain_client,
        erc20_abi=arbitrum.ERC20_ABI,
    )

    token_metadata = service.get_token_metadata(token_address=token_address)

    ERC20Token.objects.filter(pk=token_address).update(**token_metadata)

    return token_metadata
