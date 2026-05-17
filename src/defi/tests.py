from django.test import TestCase

from defi.services import UniswapService


class UniswapServiceTest(TestCase):
    def setUp(self) -> None:
        self.service = UniswapService()

    def test_make_swap(self):
        amount_in = int(0.5 * 10**6)  # 0.5 USDC (6 decimals)
        # amount_in = int(0.000190 * 10**18)  # WETH (18 decimal)

        slippage = 0.005  # 0.5%
        # slippage = 0

        usdc_token = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
        weth_token = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"

        self.service.make_swap(
            amount_in=amount_in,
            slippage=slippage,
            token_in=usdc_token,
            token_out=weth_token,
            pool_fee=500,
        )
