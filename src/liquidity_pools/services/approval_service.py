from hexbytes.main import HexBytes
from web3 import Web3

from core.clients.blockchain.blockchain_client import BlockchainClient
from core.clients.blockchain.transaction_manager import TransactionManager
from liquidity_pools.models import BlockchainTransaction


class ApprovalService:
    def __init__(
        self,
        blockchain_client: BlockchainClient,
        transaction_manager: TransactionManager,
        erc20_abi,
    ):
        self.blockchain_client = blockchain_client
        self.transaction_manager = transaction_manager
        self.erc20_abi = erc20_abi

    def approve(
        self,
        token_address: str,
        spender_address: HexBytes,
        amount: int,
    ) -> HexBytes:

        token_contract = self.blockchain_client.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=self.erc20_abi,
        )

        contract_function = token_contract.functions.approve(
            spender=spender_address,
            amount=amount,
        )

        return self.transaction_manager.execute(
            contract_function=contract_function,
            tx_type=BlockchainTransaction.TransactionType.APPROVE.value,
            gas=100000,
        )
