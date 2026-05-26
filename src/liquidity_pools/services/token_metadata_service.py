from web3 import Web3
from web3.contract import Contract
from web3.types import ChecksumAddress

from core.clients.blockchain.blockchain_client import BlockchainClient


class TokenMetadataService:
    """Service for retrieving ERC20 token metadata."""

    def __init__(
        self,
        blockchain_client: BlockchainClient,
        erc20_abi,
    ):
        self.blockchain_client = blockchain_client
        self.erc20_abi = erc20_abi

    def get_token_metadata(
        self,
        token_address: str,
    ) -> dict:
        """Retrieve token metadata."""

        token_address = Web3.to_checksum_address(
            value=token_address,
        )

        contract = self._get_contract(
            token_address=token_address,
        )

        return {
            'address': token_address,
            'name': self._safe_call(
                contract_function=contract.functions.name,
            ),
            'symbol': self._safe_call(
                contract_function=contract.functions.symbol,
                transform=str,
             ),
            'decimals': self._safe_call(
                contract_function=contract.functions.decimals,
            ),
            'total_supply': self._safe_call(
                contract_function=contract.functions.totalSupply,
            ),
            'owner': self._safe_call(
                contract_function=contract.functions.owner,
            ),
            'version': self._safe_call(
                contract_function=contract.functions.version,
                transform=str,
            ),
            'domain_separator': self._safe_call(
                contract_function=contract.functions.DOMAIN_SEPARATOR,
                transform=self._hexbytes_to_hex,
            ),
        }

    def _get_contract(
        self,
        token_address: ChecksumAddress,
    ) -> Contract | type[Contract]:
        return self.blockchain_client.w3.eth.contract(
            address=token_address,
            abi=self.erc20_abi,
        )

    @staticmethod
    def _hexbytes_to_hex(value) -> str:
        return value.hex()

    @staticmethod
    def _safe_call(
        contract_function,
        transform=None,
        default=None,
    ):
        try:
            value = contract_function().call()

            if transform:
                value = transform(value)

            return value

        except Exception:
            return default
