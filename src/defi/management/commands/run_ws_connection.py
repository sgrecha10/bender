from django.core.management import BaseCommand
import asyncio
from web3 import AsyncWeb3
from web3.providers.persistent import (
    AsyncIPCProvider,
    WebSocketProvider,
)
from django.conf import settings
from defi.utils import decode_hexbytes
from defi.models import Transaction
from asgiref.sync import sync_to_async
from attributedict.collections import AttributeDict


class Command(BaseCommand):
    help = 'Подключиться к mempool'

    def handle(self, *args, **kwargs):
        try:
            asyncio.run(self.listen_to_mempool())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Остановлено пользователем (Ctrl+C)'))

    async def listen_to_mempool(self):
        async with AsyncWeb3(WebSocketProvider('ws://172.17.0.1:32771')) as w3:
            subscription_id = await w3.eth.subscribe('newPendingTransactions')
            self.stdout.write(f'Подписка активна: {subscription_id}')

            try:
                async for message in w3.socket.process_subscriptions():
                    tx_hash = message.get("result")
                    tx_data = await w3.eth.get_transaction(tx_hash)
                    await self.handle_tx(tx_data)
                    # тут можно фильтровать по какому то адресу например
                    # if tx['to'] and tx['to'].lower() == TARGET_ADDRESS:
                    #     print(f"🔔 TX to target address: {tx_hash}")
            except Exception as e:
                pass  # транзакция может ещё не быть доступной
            finally:
                await w3.eth.unsubscribe(subscription_id)
                self.stdout.write('Подписка отменена')

    @sync_to_async
    def handle_tx(self, tx_data):
        self.stdout.write(f'Новая транзакция: {tx_data}')
        Transaction.objects.create(
            tx_hash=decode_hexbytes(tx_data['hash']),
            block_hash=tx_data['blockHash'],
            block_number=tx_data['blockNumber'],
            from_address=tx_data['from'],
            to_address=tx_data['to'],
            value=tx_data['value'],
            gas=tx_data['gas'],
            input=decode_hexbytes(tx_data['input']),
            nonce=tx_data['nonce'],
            tx_index=tx_data['transactionIndex'],
            gas_price=tx_data['gasPrice'],
            max_fee_per_gas=tx_data['maxFeePerGas'],
            max_priority_fee_per_gas=tx_data['maxPriorityFeePerGas'],
            type=tx_data['type'],
            chain_id=tx_data['chainId'],
            y_parity=tx_data['yParity'],
            access_list=tx_data['accessList'],
        )





    # НИЖЕ ПОЛНОСТЬЮ РАБОЧАЯ ПЕРВАЯ ВЕРСИЯ
    # def handle(self, *args, **options):
    #     # LOG = False  # toggle debug logging
    #     # if LOG:
    #     #     import logging
    #     #     # logger = logging.getLogger("web3.providers.AsyncIPCProvider")  # for the AsyncIPCProvider
    #     #     logger = logging.getLogger("web3.providers.WebSocketProvider")  # for the WebSocketProvider
    #     #     logger.setLevel(logging.DEBUG)
    #     #     logger.addHandler(logging.StreamHandler())
    #
    #     @sync_to_async
    #     def save_tx(tx_data: AttributeDict):
    #         print(tx_data)
    #         Transaction.objects.create(
    #             tx_hash=decode_hexbytes(tx_data['hash']),
    #             block_hash=tx_data['blockHash'],
    #             block_number=tx_data['blockNumber'],
    #             from_address=tx_data['from'],
    #             to_address=tx_data['to'],
    #             value=tx_data['value'],
    #             gas=tx_data['gas'],
    #             input=decode_hexbytes(tx_data['input']),
    #             nonce=tx_data['nonce'],
    #             tx_index=tx_data['transactionIndex'],
    #             gas_price=tx_data['gasPrice'],
    #             max_fee_per_gas=tx_data['maxFeePerGas'],
    #             max_priority_fee_per_gas=tx_data['maxPriorityFeePerGas'],
    #             type=tx_data['type'],
    #             chain_id=tx_data['chainId'],
    #             y_parity=tx_data['yParity'],
    #             access_list=tx_data['accessList'],
    #         )
    #
    #     async def context_manager_subscription_example():
    #         #  async with AsyncWeb3(AsyncIPCProvider("./path/to.filename.ipc") as w3:  # for the AsyncIPCProvider
    #         async with AsyncWeb3(WebSocketProvider(f"ws://172.17.0.1:32770")) as w3:  # for the WebSocketProvider
    #
    #             async def handler_tx(tx_hash):
    #                 try:
    #                     tx_data = await w3.eth.get_transaction(tx_hash)
    #                     await save_tx(tx_data)
    #                     # тут можно фильтровать по какому то адресу например
    #                     # if tx['to'] and tx['to'].lower() == TARGET_ADDRESS:
    #                     #     print(f"🔔 TX to target address: {tx_hash}")
    #                 except Exception as e:
    #                     pass  # транзакция может ещё не быть доступной
    #
    #             # subscribe to new block headers
    #             # subscription_id = await w3.eth.subscribe("newHeads")
    #
    #             # subscription to new transaction
    #             subscription_id = await w3.eth.subscribe("newPendingTransactions")
    #
    #             async for response in w3.socket.process_subscriptions():
    #                 # handle responses here
    #                 if tx_hash := response.get('result'):
    #                     await handler_tx(tx_hash=tx_hash)
    #
    #                 # тут надо отписываться (если надо?)
    #                 some_condition = False
    #                 if some_condition:
    #                     # unsubscribe from new block headers and break out of
    #                     # iterator
    #                     await w3.eth.unsubscribe(subscription_id)
    #                     break
    #
    #             # still an open connection, make any other requests and get
    #             # responses via send / receive
    #             latest_block = await w3.eth.get_block("latest")
    #             print(f"Latest block: {latest_block}")
    #
    #             # the connection closes automatically when exiting the context
    #             # manager (the `async with` block)
    #
    #     asyncio.run(context_manager_subscription_example())
