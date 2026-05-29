from threading import Lock

from web3 import Web3

from chains.models import Chain


class W3Service:
    _instances = {}
    _lock = Lock()

    def __new__(cls, chain_id: int) -> Web3:
        if chain_id not in cls._instances:
            with cls._lock:
                if chain_id not in cls._instances:
                    chain = Chain.objects.get(
                        id=chain_id
                    )

                    cls._instances[chain_id] = Web3(
                        Web3.HTTPProvider(
                            endpoint_uri=chain.rpc_url
                        )
                    )

        return cls._instances[chain_id]
