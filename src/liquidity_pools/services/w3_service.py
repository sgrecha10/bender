from threading import Lock

from web3 import Web3

from liquidity_pools.models import Chain


class W3Service:
    _instances = {}
    _lock = Lock()

    def __new__(cls, chain_id: int) -> Web3:
        if chain_id not in cls._instances:
            with cls._lock:
                if chain_id not in cls._instances:
                    chain = Chain.objects.get(id=chain_id)
                    cls._instances[chain_id] = cls._get_w3(rpc_urls=chain.rpc_urls)

        return cls._instances[chain_id]

    @classmethod
    def _get_w3(cls, rpc_urls: list) -> Web3:
        for rpc_url in rpc_urls:
            try:
                w3 = Web3(
                    Web3.HTTPProvider(endpoint_uri=rpc_url)
                )
                _ = w3.eth.block_number
                return w3

            except Exception:
                continue
