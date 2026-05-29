import logging

from django.conf import settings

from core.clients.uniswap.uniswap_client import UniswapClient
from defi.interfaces import arbitrum

logger = logging.getLogger(__name__)

"""
SwapService
    ├── Router
    ├── Quoter
    ├── NonceManager
    └── TransactionManager
"""

class UniswapService:
    def __init__(self) -> None:
        self.client = UniswapClient(
            rpc_url='',
            private_key=settings.WALLET_PRIVATE_KEYS['arbitrum_private_key'],
            router_address=arbitrum.ROUTER_ADDRESS,
            router_abi=arbitrum.ROUTER_ABI,
            quoter_address=arbitrum.QUOTER_ADDRESS,
            quoter_abi=arbitrum.QUOTER_ABI,
            position_manager_address=arbitrum.POSITION_MANAGER_ADDRESS,
            position_manager_abi=arbitrum.POSITION_MANAGER_ABI,
            slot0_abi=arbitrum.SLOT0_ABI,
            erc20_abi=arbitrum.ERC20_ABI,
        )

    def make_swap(
        self,
        amount_in: int,
        slippage: float | int,
        token_in: str,
        token_out: str,
        pool_fee: int,
    ):
        """Makes a swap.

        :param amount_in:
        :param slippage:
        :param token_in:
        :param token_out:
        :param pool_fee:
        """
        logger.info(f'Starting swap ... {token_in} {token_out}')

        quoted_amount = self.client.get_quotes(
            amount_in=amount_in,
            token_in=token_in,
            token_out=token_out,
            pool_fee=pool_fee,
        )

        amount_out_minimum = int(
            quoted_amount * (1 - slippage)
        )

        _ = self.client.send_approval_transaction(
            nonce=self.client.get_nonce(),
            token_contract=token_in,
            spender=self.client.router.address,
            amount=amount_in,
        )

        swap_tx_hash = self.client.send_swap_transaction(
            nonce=self.client.get_nonce(),
            amount_in=amount_in,
            amount_out_minimum=amount_out_minimum,
            token_in=token_in,
            token_out=token_out,
            pool_fee=pool_fee,
        )

        self.client.get_receipt_transaction(tx_hash=swap_tx_hash)

        logger.info(f'End swap \n{token_in} {token_out}')

    def remove_liquidity(self, token_id: int):
        """Removes liquidity.

        :param token_id: Position id.
        """
        logger.info(f'Starting remove liquidity ... {token_id}')

        position_data = self.client.get_position(token_id=token_id)

        liquidity = position_data['liquidity']

        decrease_liquidity_tx_hash = self.client.send_decrease_liquidity_transaction(
            nonce=self.client.get_nonce(),
            token_id=token_id,
            liquidity=liquidity,
        )

        collect_liquidity_tx_hash = self.client.send_collect_liquidity_transaction(
            nonce=self.client.get_nonce(),
            token_id=token_id,
        )

        self.client.get_receipt_transaction(tx_hash=decrease_liquidity_tx_hash)
        self.client.get_receipt_transaction(tx_hash=collect_liquidity_tx_hash)

        logger.info(f'End remove liquidity \n{token_id}')

    def mint_liquidity(
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
        logger.info(f'Starting mint liquidity ...\n {pool_address}')

        current_tick = self.client.get_current_tick(
            pool_address=pool_address,
        )

        tick_lower, tick_upper = (
            self.client.calculate_range_ticks(
                current_tick=current_tick,
                fee=fee,
                width=tick_width,
            )
        )

        # _ = self.client.send_approval_transaction(
        #     nonce=self.client.get_nonce(),
        #     token_contract=token0,
        #     spender=self.client.position_manager.address,
        #     amount=amount0_desired,
        # )
        #
        # _ = self.client.send_approval_transaction(
        #     nonce=self.client.get_nonce(),
        #     token_contract=token1,
        #     spender=self.client.position_manager.address,
        #     amount=amount1_desired,
        # )

        mint_tx_hash = self.client.send_mint_transaction(
            nonce=self.client.get_nonce(),
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

        if mint_tx_hash:
            self.client.get_receipt_transaction(tx_hash=mint_tx_hash)

        logger.info(f'End mint liquidity \n{pool_address}')
