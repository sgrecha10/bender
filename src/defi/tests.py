from datetime import datetime

from django.test import TestCase
from web3 import Web3

from core.clients.defi.approval_service import ApprovalService
from defi.models import BlockchainTransaction
from defi.services import UniswapService
from defi.tasks import index_blockchain_transaction_task
from core.clients.defi.uniswap_quoter_service import UniswapQuoterService

from core.clients.defi.transaction_manager import TransactionManager
from core.clients.defi.blockchain_client import BlockchainClient
from defi.interfaces import arbitrum
from django.conf import settings
from eth_account.account import Account
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


class UniswapNewServiceTest(TestCase):
    def setUp(self) -> None:
        self.usdc_token = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
        self.weth_token = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"

        self.w3 = Web3(Web3.HTTPProvider(
            endpoint_uri=settings.RPC_DATA['arbitrum_rpc_url'])
        )
        self.account = Account.from_key(
            private_key=settings.WALLET_PRIVATE_KEYS['arbitrum_private_key']
        )
        self.blockchain_client = BlockchainClient(
            w3=self.w3,
            account=self.account,
        )
        self.transaction_manager = TransactionManager(
            blockchain_client=self.blockchain_client,
            transaction_indexer_task=index_blockchain_transaction_task,
        )
        self.approval_service = ApprovalService(
            blockchain_client=self.blockchain_client,
            transaction_manager=self.transaction_manager,
            erc20_abi=arbitrum.ERC20_ABI,
        )
        self.quoter_contract = self.blockchain_client.w3.eth.contract(
            address=arbitrum.QUOTER_ADDRESS,
            abi=arbitrum.QUOTER_ABI,
        )
        self.uniswap_quoter_service = UniswapQuoterService(
            quoter_contract=self.quoter_contract,
        )

    def test_approval(self):
        router_address = arbitrum.ROUTER_ADDRESS
        router_abi = arbitrum.ROUTER_ABI
        spender = self.blockchain_client.w3.eth.contract(router_address, abi=router_abi).address

        amount = 1

        tx_hash = self.approval_service.approve(
            token_address=self.usdc_token,
            spender=spender,
            amount=amount,
        )

        receipt = self.blockchain_client.wait_for_receipt(tx_hash)

        print(receipt.get('status'))

    def test_get_quote_exact_input_single(self):
        # amount_in = int(100 * 10**6)  # usdc
        amount_in = int(1 * 10**18)  # weth

        result = self.uniswap_quoter_service.get_quote_exact_input_single(
            amount_in=amount_in,
            token_in=self.weth_token,
            token_out=self.usdc_token,
            pool_fee=500,
        )

        print(result)
