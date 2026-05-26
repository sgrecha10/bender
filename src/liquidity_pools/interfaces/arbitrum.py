"""UNISWAP Addresses and ABI Arbitrum Chain."""

import json
from pathlib import Path

from web3 import Web3

QUOTER_ADDRESS = Web3.to_checksum_address('0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6')
QUOTER_ABI = json.loads(Path('liquidity_pools/interfaces/abis/quoter.json').read_text())

ROUTER_ADDRESS = Web3.to_checksum_address('0xE592427A0AEce92De3Edee1F18E0157C05861564')
ROUTER_ABI = json.loads(Path('liquidity_pools/interfaces/abis/router.json').read_text())

POSITION_MANAGER_ADDRESS = Web3.to_checksum_address('0xC36442b4a4522E871399CD717aBDD847Ab11FE88')
POSITION_MANAGER_ABI = json.loads(Path('liquidity_pools/interfaces/abis/position_manager.json').read_text())

SLOT0_ABI = json.loads(Path('liquidity_pools/interfaces/abis/slot0.json').read_text())
ERC20_ABI = json.loads(Path('liquidity_pools/interfaces/abis/erc20.json').read_text())
