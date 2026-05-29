from django.conf import settings
from django.test import TransactionTestCase
from eth_account.account import Account
from web3 import Web3

from core.clients.blockchain.blockchain_client import BlockchainClient
from core.clients.blockchain.transaction_manager import TransactionManager
from .interfaces import arbitrum
from .services.approval_service import ApprovalService
from .services.liquidity_mint_service import LiquidityMintService
from .services.liquidity_removal_service import LiquidityRemovalService
from .services.swap_service import SwapService
from .services.token_metadata_service import TokenMetadataService
from .services.uniswap_get_position_service import UniswapGetPositionService
from .services.uniswap_quoter_service import UniswapQuoterService
from .tasks import index_blockchain_transaction_task


class LiquidityPoolServiceTest(TransactionTestCase):
    def setUp(self) -> None:
        self.usdc_token = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
        self.weth_token = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"

        self.w3 = Web3(Web3.HTTPProvider(
            endpoint_uri='')
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

        self.router_contract = self.blockchain_client.w3.eth.contract(
            address=arbitrum.ROUTER_ADDRESS,
            abi=arbitrum.ROUTER_ABI,
        )
        self.swap_service = SwapService(
            blockchain_client=self.blockchain_client,
            transaction_manager=self.transaction_manager,
            uniswap_quoter_service=self.uniswap_quoter_service,
            approval_service=self.approval_service,
            router_contract=self.router_contract,
        )

        self.position_manager_contract = self.blockchain_client.w3.eth.contract(
            address=arbitrum.POSITION_MANAGER_ADDRESS,
            abi=arbitrum.POSITION_MANAGER_ABI,
        )
        self.uniswap_get_position_service = UniswapGetPositionService(
            position_manager_contract=self.position_manager_contract,
        )

        self.liquidity_removal_service = LiquidityRemovalService(
            uniswap_get_position_service=self.uniswap_get_position_service,
            transaction_manager=self.transaction_manager,
            blockchain_client=self.blockchain_client,
            position_manager_contract=self.position_manager_contract,
        )

        self.liquidity_mint_service = LiquidityMintService(
            blockchain_client=self.blockchain_client,
            transaction_manager=self.transaction_manager,
            approval_service=self.approval_service,
            position_manager_contract=self.position_manager_contract,
            slot0_abi=arbitrum.SLOT0_ABI,
        )

        self.token_metadata_service = TokenMetadataService(
            blockchain_client=self.blockchain_client,
            erc20_abi=arbitrum.ERC20_ABI,
        )

    def test_approval(self):
        router_address = arbitrum.ROUTER_ADDRESS
        # router_abi = arbitrum.ROUTER_ABI
        # spender = self.blockchain_client.w3.eth.contract(router_address, abi=router_abi).address

        amount = 1

        tx_hash = self.approval_service.approve(
            token_address=self.usdc_token,
            spender_address=router_address,
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

    def test_swap(self):
        # amount_in = int(1 * 10**6)  # 0.5 USDC (6 decimals)
        amount_in = int(0.001 * 10**18)  # WETH (18 decimal)

        slippage = 0.005  # 0.5%

        result = self.swap_service.swap(
            amount_in=amount_in,
            slippage=slippage,
            token_in=self.weth_token,
            token_out=self.usdc_token,
            pool_fee=500,
        )

        print(result)

    def test_uniswap_get_position_service(self):
        token_id = 5496943
        result = self.uniswap_get_position_service.get_position(
            token_id=token_id,
        )

        print(result)

    def test_liquidity_removal_service(self):
        token_id = 5496943
        result = self.liquidity_removal_service.remove_liquidity(
            token_id=token_id,
            removal_percentage=100,  # 90% удаляем, 10% остается в пуле
        )

        print(result)

    def test_liquidity_mint_service(self):
        pool_address = '0xc6962004f452be9203591991d15f6b388e09e8d0'

        result = self.liquidity_mint_service.mint(
            token0=self.weth_token,
            token1=self.usdc_token,
            fee=500,
            pool_address=pool_address,
            amount0_desired=Web3.to_wei(0.5, "ether"),
            amount1_desired=int(1 * 10**6),
            tick_width=1000,
        )

        print(result)

    def test_token_metadata_service(self):
        result = self.token_metadata_service.get_token_metadata(
            token_address=self.usdc_token,
        )

        print(result)
