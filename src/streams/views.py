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
        # redis_client = StrictRedis(host='redis', port=6379, decode_responses=True)
        # data = redis_client.get('your_key_here')

        data = []
        for i in range(20):
            data.append(str(time.time()))

        data = '<br>'.join(data)
        return JsonResponse({
            'bid': data,
            'ask': data,
        })

class Dom(TemplateView):
    template_name = 'streams/dom.html'
