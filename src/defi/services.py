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
            rpc_url=settings.RPC_DATA['arbitrum_rpc_url'],
            private_key=settings.WALLET_PRIVATE_KEYS['arbitrum_private_key'],
            router_address=arbitrum.router_address,
            router_abi=arbitrum.router_abi,
            quoter_address=arbitrum.quoter_address,
            quoter_abi=arbitrum.quoter_abi,
            position_manager_address=arbitrum.position_manager_address,
            position_manager_abi=arbitrum.position_manager_abi,
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
