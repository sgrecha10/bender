from datetime import datetime, timezone

from web3 import Web3

SWAP_TOPIC = Web3.to_hex(
    Web3.keccak(
        text=(
            "Swap("
            "address,"
            "address,"
            "int256,"
            "int256,"
            "uint160,"
            "uint128,"
            "int24"
            ")"
        )
    )
)


class PoolHistoryLoaderService:
    def __init__(
        self,
        w3: Web3,
        pool_address: str,
        pool_abi: list,
    ):
        self.w3 = w3
        self.pool_address = pool_address
        self.pool_abi = pool_abi

    def load(
        self,
        from_block: int,
        to_block: int,
    ):
        pool = self.w3.eth.contract(
            address=Web3.to_checksum_address(value=self.pool_address),
            abi=self.pool_abi,
        )

        logs = self.w3.eth.get_logs({
            'address': pool.address,
            'topics': [SWAP_TOPIC],
            'fromBlock': from_block,
            'toBlock': to_block,
        })

        blocks_cache = {}

        result = []

        for log in logs:
            event = pool.events.Swap().process_log(log)

            block_number = log['blockNumber']

            if block_number not in blocks_cache:
                block = self.w3.eth.get_block(
                    block_identifier=block_number,
                )

                blocks_cache[block_number] = (
                    datetime.fromtimestamp(block['timestamp'], tz=timezone.utc)
                )

            result.append(
                {
                    'block_number': block_number,
                    'liquidity': event['args']['liquidity'],
                    'tick': event['args']['tick'],
                    'created_at': blocks_cache[block_number],
                }
            )

        return result
