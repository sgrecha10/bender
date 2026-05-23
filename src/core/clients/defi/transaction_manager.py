from .blockchain_client import BlockchainClient
from defi.decorators import retry
from web3.exceptions import Web3RPCError
from hexbytes.main import HexBytes
import logging

logger = logging.getLogger(__name__)


class TransactionManager:
    """Manages transactions sent to blockchain."""
    def __init__(
        self,
        blockchain_client: BlockchainClient,
        # transaction_indexer_task,
    ):
        self.blockchain_client = blockchain_client
        # self.transaction_indexer_task = transaction_indexer_task

    @retry(
        exceptions=(
            Web3RPCError,
            ValueError,
        ),
    )
    def execute(
        self,
        contract_function,
        gas: int = 300000,
        value: int = 0,
    ) -> HexBytes:

        # print('grecha', self.blockchain_client.w3.eth.gas_price)

        tx = contract_function.build_transaction({
            'from': self.blockchain_client.account.address,
            'nonce': self.blockchain_client.get_nonce(),
            'gas': gas,
            # 'gasPrice': self.blockchain_client.w3.eth.gas_price,  # ?????????,
            'gasPrice': self.blockchain_client.w3.to_wei('0.1', 'gwei'),
            'value': value,
        })

        signed_tx = self.blockchain_client.sign_transaction(tx)
        tx_hash = self.blockchain_client.send_raw_transaction(signed_tx)

        logger.info(
            'Transaction sent: %s',
            tx_hash.hex(),
        )

        # self.transaction_indexer_task.delay(
        #     tx_hash.hex(),
        # )

        # input_data = tx.get('input') or tx.get('data')
        # func, _ = contract.decode_function_input(data=input_data)
        # index_blockchain_transaction_task.delay(
        #     tx_hash=tx_hash,
        #     tx_type=func.fn_name,
        #     native_token_price_usdc=self.get_native_token_price_usdc(),
        #     created_at=datetime.now().isoformat(),
        # )

        return tx_hash
