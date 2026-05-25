import time

from web3 import Web3

from core.clients.defi.approval_service import ApprovalService
from core.clients.defi.blockchain_client import BlockchainClient
from core.clients.defi.transaction_manager import TransactionManager
from defi.models import BlockchainTransaction


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

    def mint(
        self,
        token0: str,
        token1: str,
        fee: int,
        pool_address: str,
        amount0_desired: int,
        amount1_desired: int,
        tick_width: int,
        amount0_min: int = 0,
        amount1_min: int = 0,
    ):

        current_tick = self._get_current_tick(
            pool_address=pool_address,
        )

        tick_lower, tick_upper = self._calculate_range_ticks(
            current_tick=current_tick,
            fee=fee,
            width=tick_width,
        )

        tx_hash = self.approval_service.approve(
            token_address=token0,
            spender_address=self.position_manager_contract.address,
            amount=amount0_desired,
        )
        self.blockchain_client.wait_for_receipt(tx_hash=tx_hash)

        tx_hash = self.approval_service.approve(
            token_address=token1,
            spender_address=self.position_manager_contract.address,
            amount=amount1_desired,
        )
        self.blockchain_client.wait_for_receipt(tx_hash=tx_hash)

        token0 = Web3.to_checksum_address(token0)
        token1 = Web3.to_checksum_address(token1)

        if token0.lower() > token1.lower():
            raise ValueError(
                "token0 must be < token1"
            )

        if tick_lower >= tick_upper:
            raise ValueError(
                'Invalid tick range'
            )

        return self._mint_liquidity(
            token0=token0,
            token1=token1,
            fee=fee,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            amount0_desired=amount0_desired,
            amount1_desired=amount1_desired,
            amount0_min=amount0_min,
            amount1_min=amount1_min,
        )

    def _get_current_tick(
        self,
        pool_address: str,
    ) -> int:
        """Retrieve current tick."""
        pool_contract = self.blockchain_client.w3.eth.contract(
            address=Web3.to_checksum_address(pool_address),
            abi=self.slot0_abi,
        )
        slot0 = pool_contract.functions.slot0().call()
        return slot0[1]

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
            int(time.time()) + 600,
        )

        contract_function = self.position_manager_contract.functions.mint(params)

        return self.transaction_manager.execute(
            contract_function=contract_function,
            tx_type=BlockchainTransaction.TransactionType.MINT.value,
            gas=1500000,
        )
