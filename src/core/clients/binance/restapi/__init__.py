from core.clients.binance.restapi.base import BinanceBaseRestClient


class BinanceClient(BinanceBaseRestClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Wallet
    from core.clients.binance.restapi.wallet import get_coins, get_trade_fee

    # Market Data
    from core.clients.binance.restapi.market_data import get_exchange_info
