# from core.clients.binance.websocket.websocket_client import BinanceWebsocketClient
#
#
# class SpotWebsocketAPIClient(BinanceWebsocketClient):
#     def __init__(
#         self,
#         stream_url="wss://ws-api.binance.com/ws-api/v3",
#         api_key=None,
#         api_secret=None,
#         on_message=None,
#         on_open=None,
#         on_close=None,
#         on_error=None,
#         on_ping=None,
#         on_pong=None,
#     ):
#         self.api_key = api_key
#         self.api_secret = api_secret
#
#         super().__init__(
#             stream_url,
#             on_message=on_message,
#             on_open=on_open,
#             on_close=on_close,
#             on_error=on_error,
#             on_ping=on_ping,
#             on_pong=on_pong,
#         )
#
#     # Market
#     from core.clients.binance.websocket.spot.websocket_api._market import ping_connectivity
#     from core.clients.binance.websocket.spot.websocket_api._market import server_time
#     from core.clients.binance.websocket.spot.websocket_api._market import exchange_info
#     from core.clients.binance.websocket.spot.websocket_api._market import order_book
#     from core.clients.binance.websocket.spot.websocket_api._market import recent_trades
#     from core.clients.binance.websocket.spot.websocket_api._market import historical_trades
#     from core.clients.binance.websocket.spot.websocket_api._market import aggregate_trades
#     from core.clients.binance.websocket.spot.websocket_api._market import klines
#     from core.clients.binance.websocket.spot.websocket_api._market import ui_klines
#     from core.clients.binance.websocket.spot.websocket_api._market import avg_price
#     from core.clients.binance.websocket.spot.websocket_api._market import ticker_24hr
#     from core.clients.binance.websocket.spot.websocket_api._market import ticker
#     from core.clients.binance.websocket.spot.websocket_api._market import ticker_price
#     from core.clients.binance.websocket.spot.websocket_api._market import ticker_book
#
#     # Account
#     from core.clients.binance.websocket.spot.websocket_api._account import account
#     from core.clients.binance.websocket.spot.websocket_api._account import order_rate_limit
#     from core.clients.binance.websocket.spot.websocket_api._account import order_history
#     from core.clients.binance.websocket.spot.websocket_api._account import oco_history
#     from core.clients.binance.websocket.spot.websocket_api._account import my_trades
#     from core.clients.binance.websocket.spot.websocket_api._account import prevented_matches
#
#     # Trade
#     from core.clients.binance.websocket.spot.websocket_api._trade import new_order
#     from core.clients.binance.websocket.spot.websocket_api._trade import new_order_test
#     from core.clients.binance.websocket.spot.websocket_api._trade import get_order
#     from core.clients.binance.websocket.spot.websocket_api._trade import cancel_order
#     from core.clients.binance.websocket.spot.websocket_api._trade import cancel_replace_order
#     from core.clients.binance.websocket.spot.websocket_api._trade import get_open_orders
#     from core.clients.binance.websocket.spot.websocket_api._trade import cancel_open_orders
#     from core.clients.binance.websocket.spot.websocket_api._trade import new_oco_order
#     from core.clients.binance.websocket.spot.websocket_api._trade import get_oco_order
#     from core.clients.binance.websocket.spot.websocket_api._trade import cancel_oco_order
#     from core.clients.binance.websocket.spot.websocket_api._trade import get_open_oco_orders
#
#     # User Data Stream
#     from core.clients.binance.websocket.spot.websocket_api._user_data import user_data_start
#     from core.clients.binance.websocket.spot.websocket_api._user_data import user_data_ping
#     from core.clients.binance.websocket.spot.websocket_api._user_data import user_data_stop
