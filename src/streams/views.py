from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404, HttpResponseBadRequest
from streams.tasks import task_diff_book_depth
from streams.handlers.depth_of_market import DepthOfMarket

from django.http import JsonResponse
from redis import StrictRedis
from datetime import datetime
import time
from django.views.generic import TemplateView
import json
from django.utils.safestring import mark_safe
from core.clients.redis_client import RedisClient


class DepthOfMarketView(View):
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action')

        if not (symbol := request.GET.get('symbol')):
            symbol = 'BTCUSDT'

        depth_of_market = DepthOfMarket()
        if action == 'start':
            depth_of_market.start(symbol)
        elif action == 'stop':
            depth_of_market.stop(symbol)

        return HttpResponse(f'{action} {symbol}. <a href="/admin">На главную</a>')


class GetRedisDataView(TemplateView):
    def get(self, request, *args, **kwargs):
        redis_conn = RedisClient()

        group_prefix_bid = 'bid'
        group_prefix_ask = 'ask'

        bid_list = redis_conn.get_dom_by_price(group_prefix_bid, end=20, desc=True)
        prepare_bid_list = []
        for price, count in bid_list:
            prepare_bid_list.append(f'<pre>{price:10}{count:12}</pre>')

        ask_list = redis_conn.get_dom_by_price(group_prefix_ask, end=20)
        prepare_ask_list = []
        for price, count in ask_list:
            prepare_ask_list.append(f'<pre>{price:10}{count:12}</pre>')

        return JsonResponse({
            'bid': prepare_bid_list,
            'ask': prepare_ask_list,
        })

    # def _get_prepare_data(self, group_prefix: str, conn):
    #     key_list = conn.keys(f'{group_prefix}*')
    #     count_list = conn.mget(key_list)
    #     union_list = list(zip(key_list, count_list))
    #
    #     prepare_union_list = list(map(lambda x: (x[0].split(":")[1], x[1]), union_list))
    #
    #     if group_prefix == 'bid:':
    #         prepare_union_list.sort(key=lambda x: float(x[0]), reverse=True)
    #     else:
    #         prepare_union_list.sort(key=lambda x: float(x[0]))
    #
    #     prepare_data = []
    #     for price, count in prepare_union_list:
    #         prepare_data.append(f'<pre>{count:25}{price:25}</pre>')
    #
    #     return ''.join(prepare_data)


class Dom(TemplateView):
    template_name = 'streams/dom.html'
