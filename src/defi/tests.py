from datetime import datetime

from django.test import TestCase
from web3 import Web3

from defi.models import BlockchainTransaction
from defi.services import UniswapService
from defi.tasks import index_blockchain_transaction_task


class UniswapServiceTest(TestCase):
    def setUp(self) -> None:
        self.service = UniswapService()
        self.usdc_token = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
        self.weth_token = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"

    def test_make_swap(self):
        # amount_in = int(0.5 * 10**6)  # 0.5 USDC (6 decimals)
        amount_in = int(0.0002 * 10**18)  # WETH (18 decimal)

        slippage = 0.005  # 0.5%
        # slippage = 0

        self.service.make_swap(
            amount_in=amount_in,
            slippage=slippage,
            token_in=self.weth_token,
            token_out=self.usdc_token,
            pool_fee=500,
        )

    def test_remove_liquidity(self):
        token_id = 5484946  # pool id
        self.service.remove_liquidity(token_id=token_id)

    def test_mint_liquidity(self):
        pool_address = '0xc6962004f452be9203591991d15f6b388e09e8d0'

        self.service.mint_liquidity(
            token0=self.weth_token,
            token1=self.usdc_token,
            fee=500,
            pool_address=pool_address,
            amount0_desired=Web3.to_wei(0.5, "ether"),
            amount1_desired=int(100 * 10**6),
            tick_width=1000,
        )

    def test_index_blockchain_transaction_task(self):
        tx_hash = '0x2367085a22fe32eac7702b4fb4330791e4dd6b50d30cc2057de4cd2efd60ee71'
        now = datetime.now()

        result = index_blockchain_transaction_task(
            tx_hash=tx_hash,
            tx_type=BlockchainTransaction.TransactionType.APPROVE.value,
            native_token_price_usdc=2137.50,
            created_at=now.isoformat(),
        )

        print(result)
