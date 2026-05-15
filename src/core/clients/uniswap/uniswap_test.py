import time
from web3 import Web3
# from django.conf import settings
from decouple import config


w3 = Web3(Web3.HTTPProvider("https://arb1.arbitrum.io/rpc"))

print(w3.is_connected())

# private_key = settings.WALLET_PRIVATE_KEYS['arbitrum_private_key']
private_key = config('ARBITRUM_PRIVATE_KEY', default='', cast=str)

account = w3.eth.account.from_key(private_key)

USDC = Web3.to_checksum_address("0xaf88d065e77c8cC2239327C5EDb3A432268e5831")
WETH = Web3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")

SWAP_ROUTER = Web3.to_checksum_address("0xE592427A0AEce92De3Edee1F18E0157C05861564")
SWAP_ROUTER_ABI = [{
    "name": "exactInputSingle",
    "type": "function",
    "stateMutability": "payable",
    "inputs": [{
        "components": [
            {"name": "tokenIn", "type": "address"},
            {"name": "tokenOut", "type": "address"},
            {"name": "fee", "type": "uint24"},
            {"name": "recipient", "type": "address"},
            {"name": "deadline", "type": "uint256"},
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMinimum", "type": "uint256"},
            {"name": "sqrtPriceLimitX96", "type": "uint160"}
        ],
        "name": "params",
        "type": "tuple"
    }],
    "outputs": [{"name": "amountOut", "type": "uint256"}]
}]

router = w3.eth.contract(address=SWAP_ROUTER, abi=SWAP_ROUTER_ABI)

amount_in = 1 * 10**6  # 1 USDC (6 decimals)

params = {
    "tokenIn": USDC,
    "tokenOut": WETH,
    "fee": 3000,
    "recipient": account.address,
    "deadline": int(time.time()) + 600,
    "amountIn": amount_in,
    "amountOutMinimum": 0,  # ⚠️ для продакшена нельзя 0
    "sqrtPriceLimitX96": 0
}

# АППРУВ

ERC20_ABI = [{
    "name": "approve",
    "type": "function",
    "stateMutability": "nonpayable",
    "inputs": [
        {"name": "spender", "type": "address"},
        {"name": "amount", "type": "uint256"}
    ],
    "outputs": [{"name": "", "type": "bool"}]
}]

token = w3.eth.contract(address=USDC, abi=ERC20_ABI)

tx = token.functions.approve(
    SWAP_ROUTER,
    amount_in
).build_transaction({
    "from": account.address,
    "nonce": w3.eth.get_transaction_count(account.address),
    "gas": 100000,
    "gasPrice": w3.to_wei("0.1", "gwei")
})

signed = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(tx_hash.hex())

#  SWAP

tx = router.functions.exactInputSingle(params).build_transaction({
    "from": account.address,
    "nonce": w3.eth.get_transaction_count(account.address) + 1,
    "gas": 300000,
    "gasPrice": w3.to_wei("0.1", "gwei")
})

signed = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

print("swap tx:", tx_hash.hex())
