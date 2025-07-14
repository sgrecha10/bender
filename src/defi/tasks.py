# from bender.celery_entry import app
# from web3 import Web3
#
#
# @app.task(bind=True)
# def task_get_uniswap_pools(self):
#     # Подключение к Ethereum-ноде (можно заменить на Infura, Alchemy и т.д.)
#     # web3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"))
#     web3 = Web3(Web3.HTTPProvider("https://eth-mainnet.g.alchemy.com/v2/13ExeNRLSC_kfst1xTDxADxx2cgLCEa3"))
#
#     # ver2
#     factory_address = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
#     start_block = 12369621  # Uniswap V3 Factory deployment block
#     end_block = web3.eth.block_number
#     step = 500
#
#     topic = web3.keccak(text="PoolCreated(address,address,uint24,int24,address)").hex()
#     all_logs = []
#
#     for block in range(start_block, end_block, step):
#         from_block = block
#         to_block = min(block + step - 1, end_block)
#
#         try:
#             logs = web3.eth.get_logs({
#                 "fromBlock": from_block,
#                 "toBlock": to_block,
#                 "address": factory_address,
#                 "topics": [topic]
#             })
#             all_logs.extend(logs)
#             # print(f"Fetched logs from blocks {from_block} to {to_block}, total so far: {len(all_logs)}")
#             print(logs)
#             print('\n')
#         except Exception as e:
#             print(f"Error at block range {from_block}-{to_block}: {e}")
