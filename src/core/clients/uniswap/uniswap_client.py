import time
from typing import Optional

from django.conf import settings
from eth_account import Account
from web3 import Web3
# from decimal import Decimal

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class UniswapClient:
    ERC20_ABI = [{
        "name": "approve",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "outputs": [{"name": "", "type": "bool"}]
    }]

    # Контракт Uniswap для Arbitrum
    SWAP_ROUTER = Web3.to_checksum_address("0xE592427A0AEce92De3Edee1F18E0157C05861564")
    SWAP_ROUTER_ABI = [{
        "name": "exactInputSingle",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [{
            "components": [
                {"name": "tokenIn", "type": "address"},
                {"name": "tokenOut", "type": "address"},
                {"name": "fee", "type": "uint24"},
                {"name": "recipient", "type": "address"},
                {"name": "deadline", "type": "uint256"},
                {"name": "amountIn", "type": "uint256"},
                {"name": "amountOutMinimum", "type": "uint256"},
                {"name": "sqrtPriceLimitX96", "type": "uint160"}
            ],
            "name": "params",
            "type": "tuple"
        }],
        "outputs": [{"name": "amountOut", "type": "uint256"}]
    }]

    def __init__(
        self,
        rpc_url: str,
        private_key: Optional[str] = None,
        # router_address: str,
    ):
        self.w3 = Web3(Web3.HTTPProvider(endpoint_uri=rpc_url))
        if private_key:
            self.private_key = private_key
            self.account = Account.from_key(private_key)
        # self.router_address = Web3.to_checksum_address(router_address)

    def is_connected(self) -> bool:
        return self.w3.is_connected()

    def approve(
        self,
        token_contract,
        spender: str,
        amount: int,
    ) -> Optional[str]:
        """Апрув расхода

        :param token_contract: какой токен тратим из кошелька
        :param spender: кто тратит, например, контракт свапа
        :param amount: сколько тратим, в минимальных единицах токена
        :return:
        """
        nonce = self.w3.eth.get_transaction_count(
            account=self.account.address,
            block_identifier="pending",
        )

        tx = token_contract.functions.approve(
            spender,
            amount
        ).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "gas": 100000,
            "gasPrice": self.w3.to_wei("0.1", "gwei")
        })
        signed = self.account.sign_transaction(tx)

        logger.info('Approval transaction is sending ...')
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(f'Sent {tx_hash.hex()}')

        logger.info('Getting receipt ...')
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 1:
            logger.info(f'Approval transaction SUCCESS, gasUsed: {receipt.gasUsed}')
            return tx_hash.hex()

        logger.error(f'Approval transaction FAIL')
        return None

    def swap_exact_input_single(
        self,
        amount_in: int,
        amount_out_minimum: int,
        token_in: str,
        token_out: str,
        pool_fee: int = 3000,
    ):
        token_in_address = Web3.to_checksum_address(token_in)
        token_out_address = Web3.to_checksum_address(token_out)

        token_in_contract = self.w3.eth.contract(
            address=token_in_address,
            abi=self.ERC20_ABI,
        )
        approve_tx = self.approve(
            token_contract=token_in_contract,
            spender=self.SWAP_ROUTER,
            amount=amount_in,
        )

        if approve_tx is None:
            return None

        router = self.w3.eth.contract(address=self.SWAP_ROUTER, abi=self.SWAP_ROUTER_ABI)

        params = {
            "tokenIn": token_in_address,
            "tokenOut": token_out_address,
            "fee": pool_fee,
            "recipient": self.account.address,
            "deadline": int(time.time()) + 600,
            "amountIn": amount_in,
            "amountOutMinimum": amount_out_minimum,  # ⚠️ для продакшена нельзя 0
            "sqrtPriceLimitX96": 0
        }

        nonce = self.w3.eth.get_transaction_count(
            account=self.account.address,
            block_identifier="pending",
        )

        tx = router.functions.exactInputSingle(params).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": self.w3.to_wei("0.1", "gwei")
        })

        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)

        logger.info('Swap transaction is sending ...')
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(f'Sent {tx_hash.hex()}')

        logger.info('Getting receipt ...')
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 1:
            logger.info(f'Swap transaction SUCCESS, gasUsed: {receipt.gasUsed}')
            return tx_hash.hex()

        logger.error(f'Swap transaction FAIL')
        return None

"""
MVP:
ERC20 wrapper
approve()
quote()
exactInputSingle()
send_transaction()

И только потом:

multihop
universal router
position manager
LP management
"""

client = UniswapClient(
    rpc_url=settings.RPC_DATA['arbitrum_rpc_url'],
    private_key=settings.WALLET_PRIVATE_KEYS['arbitrum_private_key'],
)

print(client.is_connected())

USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
WETH = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"

amount_in = int(0.1 * 10**6)  # 0.1 USDC (6 decimals)
# amount_in = int(0.000480 * 10**18)  # WETH (18 decimal)
# еще можно так:
# amount_in = w3.to_wei(Decimal("0.000480"), "ether")

res = client.swap_exact_input_single(
    amount_in=amount_in,
    amount_out_minimum=0,
    token_in=USDC,
    token_out=WETH,
    pool_fee=500,
)

print(res)
