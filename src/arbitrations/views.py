from django.http import Http404
from django.shortcuts import render
from django.views.generic import View

from arbitrations.models import Arbitration, ArbitrationDeal
from django.db.models import Sum, F, Q, Window
from django.db.models.functions.window import FirstValue, LastValue


class ResultsView(View):
    template_name = 'arbitrations/results.html'
    arbitration = None
    deal_uid_last = None
    symbol_profit_pt_last = None

    def get(self, request, *args, **kwargs):
        self.arbitration = Arbitration.objects.get(
            id=request.GET.get('arbitration_id'),
        )

        arbitration_deal_qs = ArbitrationDeal.objects.filter(
            arbitration=self.arbitration,
        ).annotate(
            symbol_profit_pt=Window(
                expression=Sum(F('price') * F('quantity')),
                partition_by=[F('deal_uid'), F('symbol')],
            ),
            open_deal_time=Window(
                expression=FirstValue('deal_time'),
                partition_by=[F('deal_uid'), F('symbol')],
                order_by='id',
            ),
            close_deal_time=Window(
                expression=LastValue('deal_time'),
                partition_by=[F('deal_uid'), F('symbol')],
                order_by='id',
            ),
            open_deal_price=Window(
                expression=FirstValue('price'),
                partition_by=[F('deal_uid'), F('symbol')],
                order_by='id',
            ),
            close_deal_price=Window(
                expression=LastValue('price'),
                partition_by=[F('deal_uid'), F('symbol')],
                order_by='id',
            ),
            open_deal_quantity=Window(
                expression=FirstValue('quantity'),
                partition_by=[F('deal_uid'), F('symbol')],
                order_by='id',
            ),
            close_deal_quantity=Window(
                expression=LastValue('quantity'),
                partition_by=[F('deal_uid'), F('symbol')],
                order_by='id',
            ),
            cause=Window(
                expression=LastValue('state'),
                partition_by=[F('deal_uid')],
                order_by='id',
            ),
        ).values(
            'deal_uid',
            'symbol',
            'symbol_profit_pt',
            'open_deal_time',
            'close_deal_time',
            'open_deal_price',
            'close_deal_price',
            'open_deal_quantity',
            'close_deal_quantity',
            'cause',
        ).distinct().exclude(
            open_deal_time=F('close_deal_time'),
        ).order_by('open_deal_time')

        closed_deals_quantity = 0
        deals_total_profit_pt = 0
        statistics = []
        for item in arbitration_deal_qs:
            statistics.append({
                'deal_number': item['deal_uid'],
                'symbol': item['symbol'],
                'open_deal_time': item['open_deal_time'],
                'close_deal_time': item['close_deal_time'],
                'open_deal_price': item['open_deal_price'],
                'close_deal_price': item['close_deal_price'],
                'open_deal_quantity': item['open_deal_quantity'],
                'close_deal_quantity': item['close_deal_quantity'],
                'symbol_profit_pt': item['symbol_profit_pt'],
            })
            if self.deal_uid_last == item['deal_uid']:
                symbol_profit_pt = item['symbol_profit_pt'] + self.symbol_profit_pt_last
                statistics.append({
                    'deal_number': item['deal_uid'],
                    'symbol': item['symbol'],
                    'open_deal_time': '',
                    'close_deal_time': '',
                    'open_deal_price': '',
                    'close_deal_price': '',
                    'open_deal_quantity': '',
                    'close_deal_quantity': '',
                    'symbol_profit_pt': '',
                    'deal_profit_pt': symbol_profit_pt,
                    'cause': item['cause'],
                })
                deals_total_profit_pt += symbol_profit_pt
                closed_deals_quantity += 1
            self.deal_uid_last = item['deal_uid']
            self.symbol_profit_pt_last = item['symbol_profit_pt']

        context = {
            'title': self.arbitration,
            'info': self._get_information(
                deals_total_profit_pt=deals_total_profit_pt,
                closed_deals_quantity=closed_deals_quantity,
            ),
            'statistics': statistics,
        }

        return render(request, self.template_name, context=context)

    def _get_information(self, deals_total_profit_pt, closed_deals_quantity):
        return {
                'arbitration_codename': self.arbitration.codename,
                'arbitration_range': f'{self.arbitration.start_time.strftime("%d.%m.%Y %H:%M")} <br> '
                                     f'{self.arbitration.end_time.strftime("%d.%m.%Y %H:%M")}',
                'arbitration_interval': self.arbitration.interval,
                'closed_deals_quantity': closed_deals_quantity,
                'deals_total_profit_pt': deals_total_profit_pt,
            }



    # def get(self, request, *args, **kwargs):
    #     self.arbitration = Arbitration.objects.get(
    #         id=request.GET.get('arbitration_id'),
    #     )
    #
    #     arbitration_deal_qs = ArbitrationDeal.objects.filter(
    #         arbitration=self.arbitration,
    #     ).order_by('id')
    #
    #     df_1 = self.arbitration.get_symbol_df(
    #         symbol_pk=self.arbitration.symbol_1_id,
    #         qs_start_time=self.arbitration.start_time,
    #         qs_end_time=self.arbitration.end_time,
    #     )
    #     df_2 = self.arbitration.get_symbol_df(
    #         symbol_pk=self.arbitration.symbol_2_id,
    #         qs_start_time=self.arbitration.start_time,
    #         qs_end_time=self.arbitration.end_time,
    #     )
    #
    #     statistics = []
    #
    #     deal_number = 0
    #     deals_total_profit_pt = 0  # по всем сделкам
    #
    #     value_names = [
    #         'symbol_1_name',
    #         'open_symbol_1_time',
    #         'open_symbol_1_price',
    #         'open_symbol_1_quantity',
    #         'close_symbol_1_time',
    #         'close_symbol_1_price',
    #         'close_symbol_1_quantity',
    #         'symbol_1_profit_pt',
    #
    #         'symbol_2_name',
    #         'open_symbol_2_time',
    #         'open_symbol_2_price',
    #         'open_symbol_2_quantity',
    #         'close_symbol_2_time',
    #         'close_symbol_2_price',
    #         'close_symbol_2_quantity',
    #         'symbol_2_profit_pt',
    #     ]
    #     item_data = dict.fromkeys(value_names)
    #
    #     for deal in arbitration_deal_qs:
    #         if deal.state == ArbitrationDeal.State.OPEN:
    #             if deal.symbol_id == self.arbitration.symbol_1_id:
    #                 item_data['symbol_1_name'] = deal.symbol
    #                 item_data['open_symbol_1_time'] = deal.deal_time
    #                 item_data['open_symbol_1_price'] = deal.price
    #                 item_data['open_symbol_1_quantity'] = deal.quantity
    #                 item_data['symbol_1_profit_pt'] = deal.price * deal.quantity
    #             elif deal.symbol_id == self.arbitration.symbol_2_id:
    #                 item_data['symbol_2_name'] = deal.symbol
    #                 item_data['open_symbol_2_time'] = deal.deal_time
    #                 item_data['open_symbol_2_price'] = deal.price
    #                 item_data['open_symbol_2_quantity'] = deal.quantity
    #                 item_data['symbol_2_profit_pt'] = deal.price * deal.quantity
    #
    #         elif deal.state == ArbitrationDeal.State.CLOSE:
    #             if deal.symbol_id == self.arbitration.symbol_1_id:
    #                 item_data['close_symbol_1_time'] = deal.deal_time
    #                 item_data['close_symbol_1_price'] = deal.price
    #                 item_data['close_symbol_1_quantity'] = deal.quantity
    #                 item_data['symbol_1_profit_pt'] += deal.price * deal.quantity
    #             elif deal.symbol_id == self.arbitration.symbol_2_id:
    #                 item_data['close_symbol_2_time'] = deal.deal_time
    #                 item_data['close_symbol_2_price'] = deal.price
    #                 item_data['close_symbol_2_quantity'] = deal.quantity
    #                 item_data['symbol_2_profit_pt'] += deal.price * deal.quantity
    #
    #         elif deal.state == ArbitrationDeal.State.CORRECTION:
    #             if deal.symbol_id == self.arbitration.symbol_1_id:
    #                 item_data['symbol_1_profit_pt'] += deal.price * deal.quantity
    #             elif deal.symbol_id == self.arbitration.symbol_2_id:
    #                 item_data['symbol_2_profit_pt'] += deal.price * deal.quantity
    #
    #         if all(item_data.values()):
    #             deal_number += 1
    #             statistics.append({
    #                 'deal_number': deal_number,
    #                 'symbol': item_data['symbol_1_name'],
    #                 'open_deal_time': item_data['open_symbol_1_time'],
    #                 'close_deal_time': item_data['close_symbol_1_time'],
    #                 'open_deal_price': item_data['open_symbol_1_price'],
    #                 'close_deal_price': item_data['close_symbol_1_price'],
    #                 'open_deal_quantity': item_data['open_symbol_1_quantity'],
    #                 'close_deal_quantity': item_data['close_symbol_1_quantity'],
    #                 'symbol_profit_pt': item_data['symbol_1_profit_pt'],
    #             })
    #             statistics.append({
    #                 'deal_number': deal_number,
    #                 'symbol': item_data['symbol_2_name'],
    #                 'open_deal_time': item_data['open_symbol_2_time'],
    #                 'close_deal_time': item_data['close_symbol_2_time'],
    #                 'open_deal_price': item_data['open_symbol_2_price'],
    #                 'close_deal_price': item_data['close_symbol_2_price'],
    #                 'open_deal_quantity': item_data['open_symbol_2_quantity'],
    #                 'close_deal_quantity': item_data['close_symbol_2_quantity'],
    #                 'symbol_profit_pt': item_data['symbol_2_profit_pt'],
    #             })
    #             deal_profit_pt = item_data['symbol_1_profit_pt'] + item_data['symbol_2_profit_pt']
    #             statistics.append({
    #                 'deal_number': deal_number,
    #                 'deal_profit_pt': deal_profit_pt,
    #             })
    #             deals_total_profit_pt += deal_profit_pt
    #             for key, _ in item_data.items():
    #                 item_data[key] = None
    #
    #     context = {
    #         'title': self.arbitration,
    #         'info': self._get_information(df_1=df_1, df_2=df_2, deals_total_profit_pt=deals_total_profit_pt),
    #         'statistics': statistics,
    #     }
    #
    #     return render(request, self.template_name, context=context)
    #
    # def _get_information(self, df_1, df_2, deals_total_profit_pt):
    #     correlation = df_1[self.arbitration.price_comparison].corr(df_2[self.arbitration.price_comparison])
    #
    #     return {
    #             'arbitration_codename': self.arbitration.codename,
    #             'arbitration_range': f'{self.arbitration.start_time.strftime("%d.%m.%Y %H:%M")} <br> '
    #                                  f'{self.arbitration.end_time.strftime("%d.%m.%Y %H:%M")}',
    #             'arbitration_interval': self.arbitration.interval,
    #             # 'closed_deals': closed_deals,
    #             'correlation': correlation,
    #             'deals_total_profit_pt': deals_total_profit_pt,
    #         }
