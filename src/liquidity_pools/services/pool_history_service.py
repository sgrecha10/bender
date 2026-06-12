from datetime import datetime, timezone
from typing import Literal

from web3 import Web3
from web3.types import BlockData

BlockIdentifier = int | Literal['latest', 'pending', 'earliest']


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
    """Получаем тики/дату через логи свопов.
    НЕ ИСПОЛЬЗУЕМ.
    """
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
                    'block_timestamp': blocks_cache[block_number],
                }
            )

        return result

    def find_block_by_timestamp(
        self,
        target_timestamp: int,
    ) -> int:
        left = 1
        right = self.w3.eth.block_number

        while left <= right:
            mid = (left + right) // 2

            block = self.w3.eth.get_block(mid)

            if block['timestamp'] < target_timestamp:
                left = mid + 1
            else:
                right = mid - 1

        return left


class PoolHistoryService:
    """Получаем тики/дату для блока."""
    def __init__(
        self,
        w3: Web3,
        pool_address: str,
        slot0: list,
    ):
        self.w3 = w3
        self.pool_address = pool_address
        self.slot0 = slot0
        self.pool_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(value=self.pool_address),
            abi=self.slot0,
        )

    def get_tick(self, block_number: BlockIdentifier = 'latest') -> int:
        pool_contract = self.pool_contract
        slot0 = pool_contract.functions.slot0().call(block_identifier=block_number)
        return slot0 and slot0[1]

    def get_block(
        self,
        block_number: BlockIdentifier = 'latest',
    ) -> BlockData:
        return self.w3.eth.get_block(block_identifier=block_number)

    def get_block_datetime(
        self,
        block: BlockData,
    ) -> datetime:
        return datetime.fromtimestamp(block['timestamp'], tz=timezone.utc)

    def get_block_number(
        self,
        block: BlockData,
    ) -> int:
        return block['number']

    def find_block_by_timestamp(
        self,
        target_timestamp: int,
    ) -> int:
        left = 1
        right = self.w3.eth.block_number

        while left <= right:
            mid = (left + right) // 2

            block = self.w3.eth.get_block(mid)

            if block['timestamp'] < target_timestamp:
                left = mid + 1
            else:
                right = mid - 1

        return left
