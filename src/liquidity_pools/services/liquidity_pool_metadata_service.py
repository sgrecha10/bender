from web3 import Web3



class LiquidityPoolMetadataService:
    def __init__(
        self,
        w3: Web3,
        slot0_abi,
    ):
        self.w3 = w3
        self.slot0_abi = slot0_abi

    def get_liquidity_pool_metadata(
        self,
        pool_address,
    ):
        pool_address_checksum = Web3.to_checksum_address(
            value=pool_address,
        )

        pool_contract = self.w3.eth.contract(
            address=pool_address_checksum,
            abi=self.slot0_abi,
        )

        fee = pool_contract.functions.fee().call()
        tick_spacing = pool_contract.functions.tickSpacing().call()

        token0_address = pool_contract.functions.token0().call()
        token1_address = pool_contract.functions.token1().call()

        return {
            'fee': fee,
            'tick_spacing': tick_spacing,
            'token0_address': token0_address,
            'token1_address': token1_address,
        }
