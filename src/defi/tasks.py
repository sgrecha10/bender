from eth_abi import decode as decode_abi
from web3 import Web3

from bender.celery_entry import app
from .models import UniswapPool
from .utils import decode_hexbytes
from django.conf import settings


@app.task(bind=True)
def task_get_uniswap_pools(self):
    # Подключение к Ethereum-ноде (можно заменить на Infura, Alchemy и т.д.)
    # web3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"))
    url = settings.ALCHEMY_CLIENT['uri'] + settings.ALCHEMY_CLIENT['token']
    web3 = Web3(Web3.HTTPProvider(url))

    # ver2
    factory_address = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
    start_block = 12369621  # Uniswap V3 Factory deployment block
    end_block = web3.eth.block_number
    step = 500

    topic = web3.keccak(text="PoolCreated(address,address,uint24,int24,address)").hex()

    for block in range(start_block, end_block, step):
        from_block = block
        to_block = min(block + step - 1, end_block)

        try:
            logs = web3.eth.get_logs({
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": factory_address,
                "topics": [topic]
            })

            for log in logs:
                # address = log['address']  # это factory_address, он не нужен
                data = log['data']
                arg_types = ['uint256', 'address']
                decoded_data = decode_abi(arg_types, data)
                topics = log['topics']
                block_hash = log['blockHash']
                block_number = log['blockNumber']
                block_timestamp = log['blockTimestamp']
                transaction_hash = log['transactionHash']
                transaction_index = log['transactionIndex']
                log_index = log['logIndex']
                removed = log['removed']

                UniswapPool.objects.update_or_create(
                    pool_address=decoded_data[1],
                    defaults={
                        'pool_type': UniswapPool.PoolType.UNISWAP_V3,
                        'token_0_address': decode_hexbytes(topics[1], kind='address'),
                        'token_1_address': decode_hexbytes(topics[2], kind='address'),
                        'fee': decode_hexbytes(topics[3], kind='int'),
                        'tick_spacing': decoded_data[0],
                        'block_hash': decode_hexbytes(block_hash),
                        'block_number': block_number,
                        'block_timestamp': decode_hexbytes(block_timestamp, kind='int'),
                        'transaction_hash': decode_hexbytes(transaction_hash),
                        'transaction_index': transaction_index,
                        'log_index': log_index,
                        'removed': removed,
                    }
                )
                # print(topics[1])
                # print(decode_hexbytes(topics[1], kind='address'))
                # print('\n')

            # all_logs.extend(logs)
            # # print(f"Fetched logs from blocks {from_block} to {to_block}, total so far: {len(all_logs)}")
            # print(logs)
            # print('\n')
        except Exception as e:
            print(f"Error at block range {from_block}-{to_block}: {e}")


@app.task(bind=True)
def task_get_txpool_content(self):
    """Запрос в mempool"""

    # import json
    # import requests
    #
    # url = "http://172.17.0.1:32769"
    # payload = {
    #     "jsonrpc": "2.0",
    #     "method": "web3_clientVersion",
    #     "params": [],
    #     "id": 1
    # }
    #
    # headers = {"Content-Type": "application/json"}
    #
    # response = requests.post(url, json=payload, headers=headers)
    # print("Status code:", response.status_code)
    # print("Response:", response.text)
    #
    # return


    # url = 'http://127.0.0.1:32769'

    # url = 'http://127.0.0.1:32769'
    url = 'http://172.17.0.1:32769'  # это IP какой имеет основной хост из докера, узнать его - ip addr show docker0

    web3 = Web3(Web3.HTTPProvider(url))
    print("Connected:", web3.is_connected())

    # Получить все транзакции из мемпула
    pending = web3.geth.txpool.content()['pending']

    print(pending)

    # Вывести все адреса и их tx
    for address, txs in pending.items():
        for nonce, tx in txs.items():
            print(
                f"{address} → {tx['to']}, "
                f"value={web3.from_wei(int(tx['value'], 16), 'ether')}"
            )
