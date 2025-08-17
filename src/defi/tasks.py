from eth_abi import decode as decode_abi
from web3 import Web3

from bender.celery_entry import app
from .models import UniswapPool, ERC20Token
from .utils import decode_hexbytes
from django.conf import settings
import time
from web3.providers.persistent import (
    AsyncIPCProvider,
    WebSocketProvider,
)

def _get_endpoint_uri():
    # Подключение к Ethereum-ноде (можно заменить на Infura, Alchemy и т.д.)
    # web3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"))
    return settings.ALCHEMY_CLIENT['uri'] + settings.ALCHEMY_CLIENT['token']


@app.task(bind=True)
def task_get_uniswap_pools_v2(self):
    web3 = Web3(Web3.HTTPProvider(endpoint_uri=_get_endpoint_uri()))

    factory_address = Web3.to_checksum_address('0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f')  # v2
    start_block = 10000835  # Uniswap V2 Factory deployment block
    end_block = web3.eth.block_number
    step = 500

    topic = web3.keccak(text="PairCreated(address,address,address,uint256)").hex()

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
                    pool_address=decode_hexbytes(decoded_data[0], kind='address'),
                    defaults={
                        'pool_type': UniswapPool.PoolType.UNISWAP_V2,
                        'token_0_address': decode_hexbytes(topics[1], kind='address'),
                        'token_1_address': decode_hexbytes(topics[2], kind='address'),
                        'fee': 3000,  # или 0.003. короче для всех пулов 0,30%
                        'block_hash': decode_hexbytes(block_hash),
                        'block_number': block_number,
                        'block_timestamp': decode_hexbytes(block_timestamp, kind='int'),
                        'transaction_hash': decode_hexbytes(transaction_hash),
                        'transaction_index': transaction_index,
                        'log_index': log_index,
                        'removed': removed,
                    }
                )

        except Exception as e:
            print(f"Error at block range {from_block}-{to_block}: {e}")


@app.task(bind=True)
def task_get_uniswap_pools_v3(self):
    web3 = Web3(Web3.HTTPProvider(endpoint_uri=_get_endpoint_uri()))

    # ver2
    factory_address = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")  # v3
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
def task_get_erc20_eip2612(self, token_address: str):
    web3 = Web3(Web3.HTTPProvider(endpoint_uri=_get_endpoint_uri()))

    ERC20_PERMIT_ABI = [
        # --- ERC20 стандарт ---
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [{"name": "owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"},
            ],
            "name": "allowance",
            "outputs": [{"name": "remaining", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "version",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "owner",
            "outputs": [{"name": "", "type": "address"}],
            "type": "function"
        },

        # --- Permit (EIP-2612) ---
        {
            "constant": False,
            "inputs": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
                {"name": "v", "type": "uint8"},
                {"name": "r", "type": "bytes32"},
                {"name": "s", "type": "bytes32"},
            ],
            "name": "permit",
            "outputs": [],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [{"name": "owner", "type": "address"}],
            "name": "nonces",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "DOMAIN_SEPARATOR",
            "outputs": [{"name": "", "type": "bytes32"}],
            "type": "function",
        },
    ]
    # token_address = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
    address = Web3.to_checksum_address(token_address)
    contract = web3.eth.contract(address=address, abi=ERC20_PERMIT_ABI)

    try:
        name = contract.functions.name().call()
    except:
        name = None

    try:
        symbol = str(contract.functions.symbol().call())
    except:
        symbol = None

    try:
        decimals = contract.functions.decimals().call()
    except:
        decimals = None

    try:
        total_supply = contract.functions.totalSupply().call()
    except:
        total_supply = None

    try:
        owner = contract.functions.owner().call()
    except:
        owner = None

    try:
        version = contract.functions.version().call()
    except:
        version = None

    try:
        domain_separator = contract.functions.DOMAIN_SEPARATOR().call()
        # print("✅ Токен поддерживает Permit (EIP-2612)")
        # print(decode_hexbytes(domain_separator))
    except:
        domain_separator = None
        # print("❌ Токен не поддерживает Permit")

    # print("Name:", name)
    # print("Symbol:", symbol)
    # print("Decimals:", decimals)
    # print("Total Supply:", total_supply)
    # # print("balanceOf:", contract.functions.balanceOf().call())
    # # print("allowance:", contract.functions.allowance().call())
    # print("Owner:", owner)
    # print("Owner:", decode_hexbytes(owner))
    # print("Version:", version)
    # print('domain_separator', decode_hexbytes(domain_separator))

    item, _ = ERC20Token.objects.update_or_create(
        address=token_address,
        defaults={
            'name': name,
            'symbol': symbol,
            'decimals': decimals,
            'total_supply': total_supply,
            'owner': decode_hexbytes(owner),
            'version': version,
            'domain_separator': decode_hexbytes(domain_separator),
        }
    )
    return item and item.pk


@app.task(bind=True)
def task_get_tokens_from_uniswap_pool(self):
    # token 0
    uniswap_pool_qs = list(
        UniswapPool.objects.all().distinct(
            'token_0_address'
        ).values_list('token_0_address', flat=True)
    )

    # i = 0
    for token in uniswap_pool_qs:
        if ERC20Token.objects.filter(address=token).exists():
            continue
        task_get_erc20_eip2612.delay(token_address=token)
        # i += 1
        # if i == 10:
        #     i = 0
        #     time.sleep(1)

    # token 1
    uniswap_pool_qs = list(
        UniswapPool.objects.all().distinct(
            'token_1_address'
        ).values_list('token_1_address', flat=True)
    )

    for token in uniswap_pool_qs:
        if ERC20Token.objects.filter(address=token).exists():
            continue
        task_get_erc20_eip2612.delay(token_address=token)
        # i += 1
        # if i == 10:
        #     i = 0
        #     time.sleep(1)


def get_uniswap_pool_liquidity_v2() -> None:
    """Получает ликвидность пула по запросу
    Это для проверки возможности, лучше использовать подписку по вебсокету.
    """

    web3 = Web3(Web3.HTTPProvider(endpoint_uri=_get_endpoint_uri()))

    # ✅ Адрес пула Uniswap V2 (пример: WETH/USDC)
    pair_address = Web3.to_checksum_address("0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc")  # address

    # ABI пула (только нужные методы)
    pair_abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "getReserves",
            "outputs": [
                {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
                {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
                {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"},
            ],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "token0",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "token1",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
    ]

    # ABI ERC20 (чтобы получить имя и decimals)
    erc20_abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function",
        },
    ]

    # Загружаем контракт пула
    pair = web3.eth.contract(address=pair_address, abi=pair_abi)

    # Получаем токены
    token0_address = pair.functions.token0().call()
    token1_address = pair.functions.token1().call()

    # Загружаем контракты токенов
    token0 = web3.eth.contract(address=token0_address, abi=erc20_abi)
    token1 = web3.eth.contract(address=token1_address, abi=erc20_abi)

    # Получаем данные токенов
    symbol0 = token0.functions.symbol().call()
    decimals0 = token0.functions.decimals().call()

    symbol1 = token1.functions.symbol().call()
    decimals1 = token1.functions.decimals().call()

    # Получаем резервы пула
    reserve0, reserve1, timestamp = pair.functions.getReserves().call()

    # Приводим к "человеческому" виду
    reserve0_norm = reserve0 / (10 ** decimals0)
    reserve1_norm = reserve1 / (10 ** decimals1)

    print(f"Pool: {symbol0}/{symbol1}")
    print(f"{symbol0}: {reserve0_norm}")
    print(f"{symbol1}: {reserve1_norm}")
    print(f"Timestamp: {timestamp}")





# ниже всякая фигня.
@app.task(bind=True)
def task_get_txpool_content(self):
    """Запрос в mempool
    Получаем мгновенный снимок
    """

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


def task_call_contract():
    url = 'http://172.17.0.1:32769'

    w3 = Web3(Web3.HTTPProvider(url))
    print('Connected:', w3.is_connected())
    assert w3.is_connected()

    # данные контракта
    contract_address = '0x1A001C36dcF27899812168503E0c2Ad3de499B7d'
    abi = [{"stateMutability": "nonpayable", "type": "function", "name": "update_data", "inputs": [{"name": "_msg", "type": "string"}, {"name": "_user", "type": "address"}, {"name": "_nums", "type": "uint256[]"}], "outputs": []}, {"stateMutability": "view", "type": "function", "name": "message", "inputs": [], "outputs": [{"name": "", "type": "string"}]}, {"stateMutability": "view", "type": "function", "name": "user", "inputs": [], "outputs": [{"name": "", "type": "address"}]}, {"stateMutability": "view", "type": "function", "name": "numbers", "inputs": [{"name": "arg0", "type": "uint256"}], "outputs": [{"name": "", "type": "uint256"}]}, {"stateMutability": "view", "type": "function", "name": "count", "inputs": [], "outputs": [{"name": "", "type": "uint256"}]}]

    contract_address = Web3.to_checksum_address(contract_address)

    contract = w3.eth.contract(
        address=contract_address,
        abi=abi,
    )

    # Данные
    message = 'Hi from Python 555'
    # recipient = '0xRecipientAddressHere'
    recipient = contract_address
    numbers = [1, 2, 3, 4]


    # account = Account.from_key(PRIVATE_KEY)  # это работает, переписать.
    account = '0x8943545177806ED17B9F23F0a21ee5948eCaa776'
    nonce = w3.eth.get_transaction_count(account)

    estimated_gas = contract.functions.update_data(message, recipient, numbers).estimate_gas({'from': account})
    print('estimated_gas', estimated_gas)

    tx = contract.functions.update_data(message, recipient, numbers).build_transaction({
        'from': account,
        'nonce': nonce,
        'gas': estimated_gas + 10_000,  # запас
        'gasPrice': w3.to_wei('5', 'gwei'),
    })

    # Подпись и отправка
    private_key = '0xbcdf20249abf0ed6d944c0288fad489e33f66b3960d9e6229c1cd214ed3bbe31'
    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print('TX sent:', tx_hash.hex())
