from eth_account import Account
from eth_account.signers.local import LocalAccount

from liquidity_pools.models import WalletAddress, Chain
from liquidity_pools.services.cryptography_service import CryptographyService


class AccountService:
    def __init__(self, wallet_address_id: int):
        self.wallet_address = WalletAddress.objects.get(id=wallet_address_id)

    def get_account(self) -> LocalAccount:
        private_key = CryptographyService.decrypt_private_key(
            payload=self.wallet_address.encrypted_private_key,
        )
        return Account.from_key(
            private_key=private_key,
        )

    def get_chain(self) -> Chain:
        return self.wallet_address.chain
