from django.core.management import BaseCommand
import asyncio
from web3 import AsyncWeb3
from web3.providers.persistent import (
    AsyncIPCProvider,
    WebSocketProvider,
)


class Command(BaseCommand):
    help = 'Запуск получения данных по пулам в цепочках'

    def handle(self, *args, **kwargs):
        try:
            asyncio.run(self.listen_to_mempool())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Остановлено пользователем (Ctrl+C)'))

    async def listen_to_mempool(self):
        async with AsyncWeb3(WebSocketProvider('ws://172.17.0.1:32771')) as w3:
            pass
