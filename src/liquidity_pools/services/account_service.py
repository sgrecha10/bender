from eth_account import Account
from eth_account.signers.local import LocalAccount

from liquidity_pools.models import WalletAddress
from liquidity_pools.services.cryptography_service import CryptographyService


class AccountService:
    def __new__(cls, wallet_address_id: int) -> LocalAccount:
        wallet_address = WalletAddress.objects.get(id=wallet_address_id)
        private_key = CryptographyService.decrypt_private_key(
            payload=wallet_address.encrypted_private_key,
        )
        return Account.from_key(
            private_key=private_key,
        )
