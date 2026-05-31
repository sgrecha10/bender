import time
from decimal import Decimal

from web3 import Web3

from core.clients.blockchain.blockchain_client import BlockchainClient
from core.clients.blockchain.transaction_manager import TransactionManager
from liquidity_pools.exceptions import TransactionFailedError
from liquidity_pools.models import BlockchainTransaction
from liquidity_pools.models import SwapRequestTransaction
from .approval_service import ApprovalService
from .uniswap_quoter_service import UniswapQuoterService


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
        swap_request_id: int,
        amount_in: int,
        slippage: Decimal | float | int,
        token_in: str,
        token_out: str,
        pool_fee: int,
        deadline_seconds: int,
    ):
        quoted_amount = self.uniswap_quoter_service.get_quote_exact_input_single(
            amount_in=amount_in,
            token_in=token_in,
            token_out=token_out,
            pool_fee=pool_fee,
        )
        amount_out_minimum = int(quoted_amount * (1 - slippage))

        allowance_result = self.approval_service.allowance(
            token_address=token_in,
            spender_address=self.router_contract.address,
            owner_address=self.blockchain_client.account.address,
        )
        if allowance_result < amount_in:
            tx_hash = self.approval_service.approve(
                token_address=token_in,
                spender_address=self.router_contract.address,
                amount=amount_in,
            )
            SwapRequestTransaction.objects.create(
                swap_request_id=swap_request_id,
                blockchain_transaction_id=tx_hash.hex(),
            )
            receipt = self.blockchain_client.wait_for_receipt(tx_hash=tx_hash)

            if receipt.get('status') != 1:
                raise TransactionFailedError(tx_hash, receipt)

        params = {
            'tokenIn': Web3.to_checksum_address(token_in),
            'tokenOut': Web3.to_checksum_address(token_out),
            'fee': pool_fee,
            'recipient': self.blockchain_client.account.address,
            'deadline': int(time.time()) + deadline_seconds,
            'amountIn': amount_in,
            'amountOutMinimum': amount_out_minimum,  # для продакшена нельзя 0
            'sqrtPriceLimitX96': 0
        }

        contract_function = self.router_contract.functions.exactInputSingle(params)
        tx_hash = self.transaction_manager.execute(
            contract_function=contract_function,
            tx_type=BlockchainTransaction.TransactionType.SWAP.value,
            gas=300000,
        )
        SwapRequestTransaction.objects.create(
            swap_request_id=swap_request_id,
            blockchain_transaction_id=tx_hash.hex(),
        )
        receipt = self.blockchain_client.wait_for_receipt(tx_hash=tx_hash)

        if receipt.get('status') != 1:
            raise TransactionFailedError(tx_hash, receipt)

        return tx_hash
