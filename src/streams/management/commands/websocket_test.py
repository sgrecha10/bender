import websocket
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Consumer'

    def handle(self, *args, **options):
        # websocket.enableTrace(True)
        # ws = websocket.WebSocket()
        # ws.connect("ws://echo.websocket.events/", origin="testing_websockets.com")
        # ws.send("Hello, Server")
        # print(ws.recv())
        # ws.close()

        # websocket.enableTrace(True)
        # ws = websocket.WebSocket()
        # ws.connect("ws://echo.websocket.events")
        # ws.ping()
        # ws.ping("This is an optional ping payload")
        # ws.close()

        def on_message(wsapp, message):
            print(message)

        def on_ping(wsapp, message):
            print("Got a ping! A pong reply has already been automatically sent.")

        def on_pong(wsapp, message):
            print("Got a pong! No need to respond")

        wsapp = websocket.WebSocketApp("wss://testnet-explorer.binance.org/ws/block",
                                       on_message=on_message, on_ping=on_ping, on_pong=on_pong)
        wsapp.run_forever(ping_interval=60, ping_timeout=10, ping_payload="This is an optional ping payload")
