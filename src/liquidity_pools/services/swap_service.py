import time

from hexbytes.main import HexBytes
from web3 import Web3

from .uniswap_quoter_service import UniswapQuoterService
from liquidity_pools.models import BlockchainTransaction
from .approval_service import ApprovalService
from core.clients.blockchain.blockchain_client import BlockchainClient
from core.clients.blockchain.transaction_manager import TransactionManager


class SwapService:
    def __init__(
        self,
        blockchain_client: BlockchainClient,
        transaction_manager: TransactionManager,
        uniswap_quoter_service: UniswapQuoterService,
        approval_service: ApprovalService,
        router_contract,
    ):
        self.blockchain_client = blockchain_client
        self.transaction_manager = transaction_manager
        self.uniswap_quoter_service = uniswap_quoter_service
        self.approval_service = approval_service
        self.router_contract = router_contract

    def swap(
        self,
        amount_in: int,
        slippage: float | int,
        token_in: str,
        token_out: str,
        pool_fee: int,
    ):
        quoted_amount = self.uniswap_quoter_service.get_quote_exact_input_single(
            amount_in=amount_in,
            token_in=token_in,
            token_out=token_out,
            pool_fee=pool_fee,
        )

        amount_out_minimum = int(
            quoted_amount * (1 - slippage)
        )

        tx_hash = self.approval_service.approve(
            token_address=token_in,
            spender_address=self.router_contract.address,
            amount=amount_in,
        )
        self.blockchain_client.wait_for_receipt(tx_hash=tx_hash)

        params = {
            'tokenIn': Web3.to_checksum_address(token_in),
            'tokenOut': Web3.to_checksum_address(token_out),
            'fee': pool_fee,
            'recipient': self.blockchain_client.account.address,
            'deadline': int(time.time()) + 600,
            'amountIn': amount_in,
            'amountOutMinimum': amount_out_minimum,  # для продакшена нельзя 0
            'sqrtPriceLimitX96': 0
        }

        contract_function = self.router_contract.functions.exactInputSingle(params)

        return self.transaction_manager.execute(
            contract_function=contract_function,
            tx_type=BlockchainTransaction.TransactionType.SWAP.value,
            gas=300000,
        )
