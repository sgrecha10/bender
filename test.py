# import json
# import requests
#
#
# # url = "http://localhost:32769"
# url = "http://172.17.0.1:32769"
#
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

# ============ АСИНХРОННОЕ ПОЛУЧЕНИЕ ТРАНЗАКЦИЙ ИЗ МЕМПУЛА (сделал в команде) ===========

import asyncio
from web3 import AsyncWeb3
from web3.providers.persistent import (
    AsyncIPCProvider,
    WebSocketProvider,
)
from django.conf import settings


LOG = True  # toggle debug logging

if LOG:
    import logging

    # logger = logging.getLogger("web3.providers.AsyncIPCProvider")  # for the AsyncIPCProvider
    logger = logging.getLogger("web3.providers.WebSocketProvider")  # for the WebSocketProvider
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

async def context_manager_subscription_example():
    #  async with AsyncWeb3(AsyncIPCProvider("./path/to.filename.ipc") as w3:  # for the AsyncIPCProvider
    async with AsyncWeb3(WebSocketProvider(f"ws://172.17.0.1:32770")) as w3:  # for the WebSocketProvider

        # subscribe to new block headers
        # subscription_id = await w3.eth.subscribe("newHeads")

        # subscription to new transaction
        subscription_id = await w3.eth.subscribe("newPendingTransactions")

        async for response in w3.socket.process_subscriptions():
            print(f"{response}\n")
            print('uri', settings.ALCHEMY_CLIENT['uri'])

            # handle responses here
            some_condition = False
            if some_condition:
                # unsubscribe from new block headers and break out of
                # iterator
                await w3.eth.unsubscribe(subscription_id)
                break


        # still an open connection, make any other requests and get
        # responses via send / receive
        latest_block = await w3.eth.get_block("latest")
        print(f"Latest block: {latest_block}")

        # the connection closes automatically when exiting the context
        # manager (the `async with` block)

asyncio.run(context_manager_subscription_example())
