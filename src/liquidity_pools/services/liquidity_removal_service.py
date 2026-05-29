import time

from core.clients.blockchain.blockchain_client import BlockchainClient
from core.clients.blockchain.transaction_manager import TransactionManager
from liquidity_pools.models import BlockchainTransaction
from .uniswap_get_position_service import UniswapGetPositionService


class LiquidityRemovalService:
    """Liquidity removal service."""

    def __init__(
        self,
        uniswap_get_position_service: UniswapGetPositionService,
        transaction_manager: TransactionManager,
        blockchain_client: BlockchainClient,
        position_manager_contract,
    ):
        self.uniswap_get_position_service = uniswap_get_position_service
        self.transaction_manager = transaction_manager
        self.blockchain_client = blockchain_client
        self.position_manager_contract = position_manager_contract

    def remove_liquidity(
        self,
        token_id: int,
        removal_percentage: int,
        deadline_seconds: int,
    ):
        position_data = self.uniswap_get_position_service.get_position(token_id=token_id)
        liquidity = position_data['liquidity']
        liquidity = int(removal_percentage * liquidity / 100)

        tx_hash = self.decrease_liquidity(
            token_id=token_id,
            liquidity=liquidity,
            deadline_seconds=deadline_seconds,
        )
        self.blockchain_client.wait_for_receipt(tx_hash=tx_hash)

        return self.collect_liquidity(
            token_id=token_id,
        )

    def decrease_liquidity(
        self,
        token_id: int,
        liquidity: int,
        deadline_seconds: int,
        amount0_min: int = 0,
        amount1_min: int = 0,
    ):
        params = {
            'tokenId': token_id,
            'liquidity': liquidity,
            'amount0Min': amount0_min,
            'amount1Min': amount1_min,
            'deadline': int(time.time()) + deadline_seconds,
        }

        contract_function = self.position_manager_contract.functions.decreaseLiquidity(params)

        return self.transaction_manager.execute(
            contract_function=contract_function,
            tx_type=BlockchainTransaction.TransactionType.DECREASE_LIQUIDITY.value,
            gas=500000,
        )

    def collect_liquidity(
        self,
        token_id: int,
        amount0_max: int = (2 ** 128 - 1),
        amount1_max: int = (2 ** 128 - 1),
    ):
        params = {
            'tokenId': token_id,
            'recipient': self.blockchain_client.account.address,
            'amount0Max': amount0_max,
            'amount1Max': amount1_max,
        }

        contract_function = self.position_manager_contract.functions.collect(params)

        return self.transaction_manager.execute(
            contract_function=contract_function,
            tx_type=BlockchainTransaction.TransactionType.COLLECT.value,
            gas=500000,
        )
