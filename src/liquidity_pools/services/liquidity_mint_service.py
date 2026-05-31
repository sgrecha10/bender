import time
from decimal import Decimal
from math import log

from web3 import Web3
from web3.contract import Contract

from core.clients.blockchain.blockchain_client import BlockchainClient
from core.clients.blockchain.transaction_manager import TransactionManager
from liquidity_pools.models import BlockchainTransaction, LiquidityMintRequestTransaction, LiquidityPool
from .approval_service import ApprovalService
from  liquidity_pools.exceptions import TransactionFailedError


class LiquidityMintService:
    """Liquidity mint service."""
    def __init__(
        self,
        blockchain_client: BlockchainClient,
        transaction_manager: TransactionManager,
        approval_service: ApprovalService,
        position_manager_contract,
        slot0_abi,
    ):
        self.blockchain_client = blockchain_client
        self.transaction_manager = transaction_manager
        self.approval_service = approval_service
        self.position_manager_contract = position_manager_contract
        self.slot0_abi = slot0_abi

    def mint_liquidity(
        self,
        liquidity_mint_request_id: int,
        liquidity_pool: LiquidityPool,
        amount0_desired: int,
        amount1_desired: int,
        range_upper_price: Decimal | float,
        range_lower_price: Decimal | float,
        amount0_min: int,  # 0
        amount1_min: int,  # 0
        slippage_percent: Decimal | float | int,
        deadline_seconds: int,
    ):
        token0_address = Web3.to_checksum_address(
            value=liquidity_pool.token0.address,
        )
        token1_address = Web3.to_checksum_address(
            value=liquidity_pool.token1.address,
        )
        if token0_address.lower() > token1_address.lower():
            raise ValueError('token0 must be < token1')

        fee = liquidity_pool.fee
        tick_spacing = liquidity_pool.tick_spacing

        tick_lower, tick_upper = self._calculate_ticks(
            lower_price=range_lower_price,
            upper_price=range_upper_price,
            token0_decimals=liquidity_pool.token0.decimals,
            token1_decimals=liquidity_pool.token1.decimals,
            tick_spacing=tick_spacing,
        )
        if tick_lower >= tick_upper:
            raise ValueError('Invalid tick range')

        ## Апрувим оба токена в кошельке
        approve_input = [
            (token0_address, amount0_desired),
            (token1_address, amount1_desired),
        ]
        for token, amount_desired in approve_input:
            allowance_result = self.approval_service.allowance(
                token_address=token,
                spender_address=self.position_manager_contract.address,
                owner_address=self.blockchain_client.account.address,
            )

            if allowance_result < amount_desired:
                tx_hash = self.approval_service.approve(
                    token_address=token,
                    spender_address=self.position_manager_contract.address,
                    amount=amount_desired,
                )
                LiquidityMintRequestTransaction.objects.create(
                    liquidity_mint_request_id=liquidity_mint_request_id,
                    blockchain_transaction_id=tx_hash.hex(),
                )
                receipt = self.blockchain_client.wait_for_receipt(tx_hash=tx_hash)
                if receipt.get('status') != 1:
                    raise TransactionFailedError(tx_hash, receipt)

        tx_hash = self._mint_liquidity(
            token0_address=token0_address,
            token1_address=token1_address,
            fee=fee,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            amount0_desired=amount0_desired,
            amount1_desired=amount1_desired,
            amount0_min=amount0_min,
            amount1_min=amount1_min,
            deadline_seconds=deadline_seconds,
        )
        LiquidityMintRequestTransaction.objects.create(
            liquidity_mint_request_id=liquidity_mint_request_id,
            blockchain_transaction_id=tx_hash.hex(),
        )
        receipt = self.blockchain_client.wait_for_receipt(tx_hash=tx_hash)
        if receipt.get('status') != 1:
            raise TransactionFailedError(tx_hash, receipt)

        return tx_hash

    def _mint_liquidity(
        self,
        token0_address: str,
        token1_address: str,
        fee: int,
        tick_lower: int,
        tick_upper: int,
        amount0_desired: int,
        amount1_desired: int,
        amount0_min: int,
        amount1_min: int,
        deadline_seconds: int,
    ):
        params = (
            token0_address,
            token1_address,
            fee,
            tick_lower,
            tick_upper,
            amount0_desired,
            amount1_desired,
            amount0_min,
            amount1_min,
            self.blockchain_client.account.address,
            int(time.time()) + deadline_seconds,
        )

        contract_function = self.position_manager_contract.functions.mint(params)

        contract_function.call({
            'from': self.blockchain_client.account.address
        })

        contract_function.estimate_gas({
            'from': self.blockchain_client.account.address,
        })

        return self.transaction_manager.execute(
            contract_function=contract_function,
            tx_type=BlockchainTransaction.TransactionType.MINT.value,
            gas=1500000,
        )

    def _price_to_tick(
        self,
        price: Decimal | float,
        token0_decimals: int,
        token1_decimals: int,
    ) -> int:
        price_internal = (
            float(price) * 10 ** (token1_decimals - token0_decimals)
        )
        return int(log(price_internal) / log(1.0001))

    def _calculate_ticks(
        self,
        lower_price: Decimal | float,
        upper_price: Decimal | float,
        token0_decimals: int,
        token1_decimals: int,
        tick_spacing: int,
    ) -> tuple[int, int]:
        tick_lower = self._price_to_tick(lower_price, token0_decimals, token1_decimals)
        tick_upper = self._price_to_tick(upper_price, token0_decimals, token1_decimals)

        tick_lower = (tick_lower // tick_spacing) * tick_spacing
        tick_upper = (tick_upper // tick_spacing) * tick_spacing

        return tick_lower, tick_upper
