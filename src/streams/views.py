from django.views.generic.base import View
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.generic.base import View

from core.clients.redis_client import RedisClient
from streams.handlers.depth_of_market import DepthOfMarketStream


class DepthOfMarketView(View):
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action')

        if not (symbol := request.GET.get('symbol')):
            symbol = 'BTCUSDT'

        depth_of_market = DepthOfMarketStream()
        if action == 'start':
            depth_of_market.run(symbol)
        elif action == 'stop':
            depth_of_market.stop(symbol)

        return HttpResponse(f'{action} {symbol}. <a href="/admin">На главную</a>')


class GetRedisDataView(TemplateView):
    def get(self, request, *args, **kwargs):
        redis_conn = RedisClient()

        group_prefix_bid = 'bid'
        group_prefix_ask = 'ask'

        bid_list = redis_conn.get_dom_by_price(group_prefix_bid, end=120, desc=True)
        prepare_bid_list = []
        for price, count in bid_list:
            prepare_bid_list.append(f'<pre>{price:10}{count:12}</pre>')

        ask_list = redis_conn.get_dom_by_price(group_prefix_ask, end=120)
        prepare_ask_list = []
        for price, count in ask_list:
            prepare_ask_list.append(f'<pre>{price:10}{count:12}</pre>')

        return JsonResponse({
            'bid': prepare_bid_list,
            'ask': prepare_ask_list,
        })


class Dom(TemplateView):
    template_name = 'streams/dom.html'
