from django.conf import settings
from web3 import Web3

from core.clients.blockchain.blockchain_client import BlockchainClient
from core.clients.blockchain.transaction_manager import TransactionManager
from ..interfaces import arbitrum
from ..services.account_service import AccountService
from ..services.approval_service import ApprovalService
from ..services.liquidity_mint_service import LiquidityMintService
from ..services.liquidity_removal_service import LiquidityRemovalService
from ..services.swap_service import SwapService
from ..services.token_metadata_service import TokenMetadataService
from ..services.uniswap_get_position_service import UniswapGetPositionService
from ..services.uniswap_quoter_service import UniswapQuoterService


class ArbitrumContainer:
    def __init__(self, wallet_address_id: int):
        self.w3 = Web3(Web3.HTTPProvider(
            endpoint_uri=settings.RPC_DATA['arbitrum_rpc_url'])
        )
        self.account = AccountService(
            wallet_address_id=wallet_address_id,
        )
        self.blockchain_client = BlockchainClient(
            w3=self.w3,
            account=self.account,
        )
        self.transaction_manager = TransactionManager(
            blockchain_client=self.blockchain_client,
            transaction_indexer_task=self._get_transaction_indexer_task(),
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
            w3=self.w3,
            erc20_abi=arbitrum.ERC20_ABI,
        )

    def _get_transaction_indexer_task(self):
        """Lazy load transaction indexer task."""
        from liquidity_pools.tasks import index_blockchain_transaction_task
        return index_blockchain_transaction_task
