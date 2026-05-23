from eth_account.datastructures import SignedTransaction
from eth_account.signers.local import LocalAccount
from hexbytes.main import HexBytes
from web3 import Web3
from web3.types import TxReceipt


class BlockchainClient:
    """Low level client to interact with blockchain."""
    def __init__(
        self,
        w3: Web3,
        account: LocalAccount,
    ):
        self.w3 = w3
        self.account = account
        self.nonce = None

    def get_nonce(self) -> int:
        if self.nonce is None:
            self.nonce = self.w3.eth.get_transaction_count(
                account=self.account.address,
                block_identifier='pending',
            )
        nonce = self.nonce
        self.nonce += 1
        return nonce

    def sign_transaction(
        self,
        tx: dict,
    ) -> SignedTransaction:
        return self.account.sign_transaction(transaction_dict=tx)

    def send_raw_transaction(
        self,
        signed_tx,
    ) -> HexBytes:
        return self.w3.eth.send_raw_transaction(
            transaction=signed_tx.raw_transaction,
        )

    def wait_for_receipt(
        self,
        tx_hash: HexBytes,
    ) -> TxReceipt:
        return self.w3.eth.wait_for_transaction_receipt(
            transaction_hash=tx_hash,
        )
