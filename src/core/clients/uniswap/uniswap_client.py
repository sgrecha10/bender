import logging
import time

from eth_account import Account
from hexbytes.main import HexBytes
from web3 import Web3
from web3.exceptions import Web3RPCError
from web3.types import TxReceipt

from defi.decorators import retry

logger = logging.getLogger(__name__)


class UniswapClient:
    def __init__(
        self,
        rpc_url: str,
        private_key: str,
        router_address: str,
        router_abi: list,
        quoter_address: str,
        quoter_abi: list,
    ):
        self.w3 = Web3(Web3.HTTPProvider(endpoint_uri=rpc_url))
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.nonce = None
        self.router_address = Web3.to_checksum_address(router_address)
        self.router_abi = router_abi
        self.quoter_address = Web3.to_checksum_address(quoter_address)
        self.quoter_abi = quoter_abi

    def is_connected(self) -> bool:
        return self.w3.is_connected()

    def get_nonce(self) -> int:
        """Возвращает актуальный nonce."""
        if self.nonce is None:
            self.nonce = self.w3.eth.get_transaction_count(
                account=self.account.address,
                block_identifier="pending",
            )
        nonce = self.nonce
        self.nonce += 1
        return nonce

    @retry(exceptions=(Web3RPCError,))
    def send_approval_transaction(
        self,
        nonce: int,
        token_contract: str,
        spender: str,
        amount: int,
    ) -> HexBytes:
        """Send approval transaction.

        :param token_contract:
        :param spender:
        :param amount: в минимальных единицах токена
        :param nonce:
        :return:
        """
        token_contract_checksum = Web3.to_checksum_address(token_contract)
        erc20_abi = [{
            "name": "approve",
            "type": "function",
            "stateMutability": "nonpayable",
            "inputs": [
                {"name": "spender", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ],
            "outputs": [{"name": "", "type": "bool"}]
        }]
        token_contract = self.w3.eth.contract(
            address=token_contract_checksum,
            abi=erc20_abi,
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

        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(f'Approval transaction sent {tx_hash.hex()}')

        return tx_hash

    def get_receipt_transaction(
        self,
        tx_hash: HexBytes,
    ) -> TxReceipt:
        """Retrieve a transaction receipt.

        :param tx_hash:
        :return:
        """
        logger.info(f'Waiting for receipt ... {tx_hash.hex()}')
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.get('status') == 1:
            logger.info(f'Transaction SUCCESS {tx_hash.hex()}, gasUsed: {receipt.get("gasUsed")}')
        else:
            logger.error(f'Transaction FAIL {tx_hash.hex()}, gasUsed: {receipt.get("gasUsed")}')

        return receipt

    @retry(exceptions=(Web3RPCError,))
    def send_swap_transaction(
        self,
        nonce: int,
        amount_in: int,
        amount_out_minimum: int,
        token_in: str,
        token_out: str,
        pool_fee: int,
    ) -> HexBytes:
        """Send swap transaction.

        :param nonce:
        :param amount_in:
        :param amount_out_minimum:
        :param token_in:
        :param token_out:
        :param pool_fee:
        :return:
        """
        router = self.w3.eth.contract(
            address=self.router_address,
            abi=self.router_abi,
        )

        params = {
            "tokenIn": Web3.to_checksum_address(token_in),
            "tokenOut": Web3.to_checksum_address(token_out),
            "fee": pool_fee,
            "recipient": self.account.address,
            "deadline": int(time.time()) + 600,
            "amountIn": amount_in,
            "amountOutMinimum": amount_out_minimum,  # для продакшена нельзя 0
            "sqrtPriceLimitX96": 0
        }

        tx = router.functions.exactInputSingle(params).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": self.w3.to_wei("0.1", "gwei")
        })

        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)

        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(f'Swap transaction sent {tx_hash.hex()}')

        return tx_hash

    def get_quotes(
        self,
        amount_in: int,
        token_in: str,
        token_out: str,
        pool_fee: int,
    ) -> int:
        """Retrieve quotes.

        :param amount_in:
        :param token_in:
        :param token_out:
        :param pool_fee:
        :return:
        """
        quoter = self.w3.eth.contract(
            address=self.quoter_address,
            abi=self.quoter_abi,
        )

        params = {
            "tokenIn": Web3.to_checksum_address(token_in),
            "tokenOut": Web3.to_checksum_address(token_out),
            "fee": pool_fee,
            "amountIn": amount_in,
            "sqrtPriceLimitX96": 0,
        }

        amount_out = quoter.functions.quoteExactInputSingle(**params).call()

        logger.info(f'Amount_out {amount_out}')
        return amount_out
