from market_data.constants import Interval


"""
https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints
seconds	1s
minutes	1m, 3m, 5m, 15m, 30m
hours	1h, 2h, 4h, 6h, 8h, 12h
days	1d, 3d
weeks	1w
months	1M
"""
BINANCE_INTERVAL_MAP = {
    Interval.MINUTE_1: '1m',
}
