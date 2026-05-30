import time
from decimal import Decimal

from web3 import Web3
from web3.contract import ContractConstructor, Contract

from core.clients.blockchain.blockchain_client import BlockchainClient
from core.clients.blockchain.transaction_manager import TransactionManager
from liquidity_pools.models import BlockchainTransaction, LiquidityMintRequestTransaction
from .approval_service import ApprovalService
from  liquidity_pools.exceptions import TransactionFailedError


class LiquidityMintService:
    """Liquidity mint service."""
    TICK_SPACING = {
        100: 1,
        500: 10,
        3000: 60,
        10000: 200,
    }

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
        token0: str,
        token1: str,
        pool_address: str,
        amount0_desired: int,
        amount1_desired: int,
        tick_width: int,
        range_upper_limit: int,
        range_lower_limit: int,
        amount0_min: int,  # 0
        amount1_min: int,  # 0
        slippage_percent: Decimal | float | int,
        deadline_seconds: int,
    ):
        ### Вычисляем tick_lower, tick_upper
        ## Сначала просто по tick_width вверх и вниз - проверим цену.
        pool_contract = self._get_pool_contract(pool_address=pool_address)
        slot0 = pool_contract.functions.slot0().call()
        current_tick = slot0[1]
        fee = pool_contract.functions.fee().call()
        tick_lower, tick_upper = self._calculate_range_ticks(
            current_tick=current_tick,
            fee=fee,
            width=tick_width,
        )
        if tick_lower >= tick_upper:
            raise ValueError('Invalid tick range')

        ## Апрувим оба токена в кошельке
        approve_input = [
            (token0, amount0_desired),
            (token1, amount1_desired),
        ]
        for token, amount_desired in approve_input:  # прикрутить алловансе!!!!!!!!!!!!!
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

        ## Выполняем минт
        token0 = Web3.to_checksum_address(token0)
        token1 = Web3.to_checksum_address(token1)
        if token0.lower() > token1.lower():
            raise ValueError('token0 must be < token1')

        tx_hash = self._mint_liquidity(
            token0=token0,
            token1=token1,
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

    def _get_pool_contract(
        self,
        pool_address: str,
    ) -> Contract | type[Contract]:
        checksum_address_pool = Web3.to_checksum_address(pool_address)
        return self.blockchain_client.w3.eth.contract(
            address=checksum_address_pool,
            abi=self.slot0_abi,
        )

    def _calculate_range_ticks(
        self,
        current_tick: int,
        fee: int,
        width: int,
    ):
        tick_lower = current_tick - width
        tick_upper = current_tick + width

        tick_lower = self._align_tick_to_spacing(
            tick=tick_lower,
            fee=fee,
        )
        tick_upper = self._align_tick_to_spacing(
            tick=tick_upper,
            fee=fee,
        )
        return tick_lower, tick_upper

    def _align_tick_to_spacing(
        self,
        tick: int,
        fee: int,
    ) -> int:
        spacing = self.TICK_SPACING[fee]
        return (tick // spacing) * spacing

    def _mint_liquidity(
        self,
        token0: str,
        token1: str,
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
            token0,
            token1,
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

        return self.transaction_manager.execute(
            contract_function=contract_function,
            tx_type=BlockchainTransaction.TransactionType.MINT.value,
            gas=1500000,
        )
