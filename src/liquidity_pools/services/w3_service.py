from threading import Lock

from web3 import Web3

from liquidity_pools.models import Chain


class W3Service:
    _instances: dict[int, Web3] = {}
    _lock = Lock()

    def __new__(cls, chain_id: int) -> Web3:
        w3 = cls._instances.get(chain_id)
        if w3:
            try:
                _ = w3.eth.block_number
                return w3

            except Exception:
                cls._instances.pop(chain_id, None)

        with cls._lock:
            chain = Chain.objects.get(id=chain_id)
            w3 = cls._get_w3(rpc_urls=chain.rpc_urls)

            cls._instances[chain_id] = w3

            return w3

    @classmethod
    def _get_w3(
        cls,
        rpc_urls: list[str],
    ) -> Web3:
        last_exception = None

        for rpc_url in rpc_urls:
            try:
                w3 = Web3(
                    Web3.HTTPProvider(
                        endpoint_uri=rpc_url,
                        request_kwargs={
                            'timeout': 30,
                        },
                    ),
                )

                _ = w3.eth.block_number

                return w3

            except Exception as e:
                last_exception = e

        raise last_exception

    @classmethod
    def reset(cls, chain_id: int):
        """На всякий случай."""
        cls._instances.pop(chain_id, None)
