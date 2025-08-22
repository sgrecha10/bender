import asyncio

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management import BaseCommand
from eth_utils import event_abi_to_log_topic
from web3 import AsyncWeb3
from web3._utils.events import get_event_data
from web3.providers.persistent import (
    WebSocketProvider,
)

from defi.models import PoolLiquidity

# Адрес пула Uniswap V2 (пример: WETH/USDC)
pair_address = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"

# ABI события Sync
sync_event_abi = {
    "anonymous": False,
    "inputs": [
        {"indexed": False, "internalType": "uint112", "name": "reserve0", "type": "uint112"},
        {"indexed": False, "internalType": "uint112", "name": "reserve1", "type": "uint112"},
    ],
    "name": "Sync",
    "type": "event",
}

class Command(BaseCommand):
    help = 'Запуск получения данных по пулам в цепочках'

    def handle(self, *args, **kwargs):
        PoolLiquidity.objects.all().delete()
        try:
            asyncio.run(self.get_liquidity())
        except KeyboardInterrupt:
            PoolLiquidity.objects.all().delete()
            self.stdout.write(self.style.WARNING('Остановлено пользователем (Ctrl+C)'))

    def _get_endpoint_uri(self):
        return settings.ALCHEMY_CLIENT['ws_uri'] + settings.ALCHEMY_CLIENT['token']

    async def get_liquidity(self):
        async with AsyncWeb3(WebSocketProvider(endpoint_uri=self._get_endpoint_uri())) as w3:
            sync_topic = event_abi_to_log_topic(sync_event_abi)
            subscription_id = await w3.eth.subscribe("logs", {"address": pair_address})

            async for event in w3.socket.process_subscriptions():
                log = event.get("result")
                if not log:
                    continue

                if log["topics"][0].hex() == sync_topic.hex():
                    decoded = get_event_data(w3.codec, sync_event_abi, log)
                    await self.handle_event(data=decoded)

    @sync_to_async
    def handle_event(self, data):
        reserve0 = data["args"]["reserve0"]
        reserve1 = data["args"]["reserve1"]
        self.stdout.write(f'Reserves: {reserve0} / {reserve1}')

        PoolLiquidity.objects.update_or_create(
            pool_id=pair_address.lower(),
            defaults={
                'reserve0': reserve0,
                'reserve1': reserve1,
            }
        )
