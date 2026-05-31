import logging

from hexbytes.main import HexBytes
from web3.exceptions import Web3RPCError

from liquidity_pools.decorators import retry
from liquidity_pools.models import BlockchainTransaction
from .blockchain_client import BlockchainClient

logger = logging.getLogger(__name__)


class TransactionManager:
    """Manages transactions sent to blockchain."""
    def __init__(
        self,
        blockchain_client: BlockchainClient,
        transaction_indexer_task,
    ):
        self.blockchain_client = blockchain_client
        self.transaction_indexer_task = transaction_indexer_task

    @retry(
        exceptions=(
            Web3RPCError,
            ValueError,
        ),
    )
    def execute(
        self,
        contract_function,
        tx_type: str,
        gas: int = 300000,
        value: int = 0,
    ) -> HexBytes:

        tx = contract_function.build_transaction({
            'from': self.blockchain_client.account.address,
            'nonce': self.blockchain_client.get_nonce(),
            'gas': gas,
            'gasPrice': int(self.blockchain_client.w3.eth.gas_price * 1.3),
            # 'gasPrice': self.blockchain_client.w3.to_wei('0.1', 'gwei'),
            'value': value,
        })

        signed_tx = self.blockchain_client.sign_transaction(tx)
        tx_hash = self.blockchain_client.send_raw_transaction(signed_tx)

        logger.info(
            'Transaction sent: %s',
            tx_hash.hex(),
        )

        BlockchainTransaction.objects.create(
            tx_hash=tx_hash.hex(),
            chain_id=self.blockchain_client.w3.eth.chain_id,
            tx_type=tx_type,
        )

        # тут дублируется chain_id, tx_type
        # оставил что бы эта таска могла создавать транзакции (не знаю, надо ли это, подумать)
        self.transaction_indexer_task.delay(
            chain_id=self.blockchain_client.w3.eth.chain_id,
            tx_hash=tx_hash.hex(),
            tx_type=tx_type,
        )

        return tx_hash
