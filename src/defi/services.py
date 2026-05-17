import logging
from decimal import Decimal

from django.conf import settings

from core.clients.uniswap.uniswap_client import UniswapClient

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
            router_address=settings.SWAP_POOL_DATA['swap_router'],
            router_abi=settings.SWAP_POOL_DATA['swap_router_abi'],
            quoter_address=settings.SWAP_POOL_DATA['swap_quoter'],
            quoter_abi=settings.SWAP_POOL_DATA['swap_quoter_abi'],
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
            spender=self.client.router_address,
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

        logger.info(f'End swap {token_in} {token_out}')
