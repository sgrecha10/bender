class BlockchainTransactionError(Exception):
    pass


class TransactionFailedError(BlockchainTransactionError):
    def __init__(
            self,
            tx_hash,
            receipt=None,
    ):
        self.tx_hash = tx_hash
        self.receipt = receipt

        super().__init__(
            f'Transaction {tx_hash} failed. With receipt: {receipt}'
        )
