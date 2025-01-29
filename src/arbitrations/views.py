from django.http import Http404
from django.shortcuts import render
from django.views.generic import View

from arbitrations.models import Arbitration, ArbitrationDeal


class ResultsView(View):
    template_name = 'arbitrations/results.html'
    arbitration = None

    def get(self, request, *args, **kwargs):
        self.arbitration = Arbitration.objects.get(
            id=request.GET.get('arbitration_id'),
        )

        arbitration_deal_qs = ArbitrationDeal.objects.filter(
            arbitration=self.arbitration,
        ).order_by('id')

        df_1 = self.arbitration.get_symbol_df(
            symbol_pk=self.arbitration.symbol_1_id,
            qs_start_time=self.arbitration.start_time,
            qs_end_time=self.arbitration.end_time,
        )
        df_2 = self.arbitration.get_symbol_df(
            symbol_pk=self.arbitration.symbol_2_id,
            qs_start_time=self.arbitration.start_time,
            qs_end_time=self.arbitration.end_time,
        )

        statistics = []

        deal_number = 0
        deals_total_profit_pt = 0  # по всем сделкам

        value_names = [
            'symbol_1_name',
            'open_symbol_1_time',
            'open_symbol_1_price',
            'open_symbol_1_quantity',
            'close_symbol_1_time',
            'close_symbol_1_price',
            'close_symbol_1_quantity',
            'symbol_1_profit_pt',

            'symbol_2_name',
            'open_symbol_2_time',
            'open_symbol_2_price',
            'open_symbol_2_quantity',
            'close_symbol_2_time',
            'close_symbol_2_price',
            'close_symbol_2_quantity',
            'symbol_2_profit_pt',
        ]
        item_data = dict.fromkeys(value_names)

        for deal in arbitration_deal_qs:
            if deal.state == ArbitrationDeal.State.OPEN:
                if deal.symbol_id == self.arbitration.symbol_1_id:
                    item_data['symbol_1_name'] = deal.symbol
                    item_data['open_symbol_1_time'] = deal.deal_time
                    item_data['open_symbol_1_price'] = deal.price
                    item_data['open_symbol_1_quantity'] = deal.quantity
                    item_data['symbol_1_profit_pt'] = deal.price * deal.quantity
                elif deal.symbol_id == self.arbitration.symbol_2_id:
                    item_data['symbol_2_name'] = deal.symbol
                    item_data['open_symbol_2_time'] = deal.deal_time
                    item_data['open_symbol_2_price'] = deal.price
                    item_data['open_symbol_2_quantity'] = deal.quantity
                    item_data['symbol_2_profit_pt'] = deal.price * deal.quantity

            elif deal.state == ArbitrationDeal.State.CLOSE:
                if deal.symbol_id == self.arbitration.symbol_1_id:
                    item_data['close_symbol_1_time'] = deal.deal_time
                    item_data['close_symbol_1_price'] = deal.price
                    item_data['close_symbol_1_quantity'] = deal.quantity
                    item_data['symbol_1_profit_pt'] += deal.price * deal.quantity
                elif deal.symbol_id == self.arbitration.symbol_2_id:
                    item_data['close_symbol_2_time'] = deal.deal_time
                    item_data['close_symbol_2_price'] = deal.price
                    item_data['close_symbol_2_quantity'] = deal.quantity
                    item_data['symbol_2_profit_pt'] += deal.price * deal.quantity

            elif deal.state == ArbitrationDeal.State.CORRECTION:
                if deal.symbol_id == self.arbitration.symbol_1_id:
                    item_data['symbol_1_profit_pt'] += deal.price * deal.quantity
                elif deal.symbol_id == self.arbitration.symbol_2_id:
                    item_data['symbol_2_profit_pt'] += deal.price * deal.quantity

            if all(item_data.values()):
                deal_number += 1
                statistics.append({
                    'deal_number': deal_number,
                    'symbol': item_data['symbol_1_name'],
                    'open_deal_time': item_data['open_symbol_1_time'],
                    'close_deal_time': item_data['close_symbol_1_time'],
                    'open_deal_price': item_data['open_symbol_1_price'],
                    'close_deal_price': item_data['close_symbol_1_price'],
                    'open_deal_quantity': item_data['open_symbol_1_quantity'],
                    'close_deal_quantity': item_data['close_symbol_1_quantity'],
                    'symbol_profit_pt': item_data['symbol_1_profit_pt'],
                })
                statistics.append({
                    'deal_number': deal_number,
                    'symbol': item_data['symbol_2_name'],
                    'open_deal_time': item_data['open_symbol_2_time'],
                    'close_deal_time': item_data['close_symbol_2_time'],
                    'open_deal_price': item_data['open_symbol_2_price'],
                    'close_deal_price': item_data['close_symbol_2_price'],
                    'open_deal_quantity': item_data['open_symbol_2_quantity'],
                    'close_deal_quantity': item_data['close_symbol_2_quantity'],
                    'symbol_profit_pt': item_data['symbol_2_profit_pt'],
                })
                deal_profit_pt = item_data['symbol_1_profit_pt'] + item_data['symbol_2_profit_pt']
                statistics.append({
                    'deal_number': deal_number,
                    'deal_profit_pt': deal_profit_pt,
                })
                deals_total_profit_pt += deal_profit_pt
                for key, _ in item_data.items():
                    item_data[key] = None

        context = {
            'title': self.arbitration,
            'info': self._get_information(df_1=df_1, df_2=df_2, deals_total_profit_pt=deals_total_profit_pt),
            'statistics': statistics,
        }

        return render(request, self.template_name, context=context)

    def _get_information(self, df_1, df_2, deals_total_profit_pt):
        correlation = df_1[self.arbitration.price_comparison].corr(df_2[self.arbitration.price_comparison])

        return {
                'arbitration_codename': self.arbitration.codename,
                'arbitration_range': f'{self.arbitration.start_time.strftime("%d.%m.%Y %H:%M")} <br> '
                                     f'{self.arbitration.end_time.strftime("%d.%m.%Y %H:%M")}',
                'arbitration_interval': self.arbitration.interval,
                # 'closed_deals': closed_deals,
                'correlation': correlation,
                'deals_total_profit_pt': deals_total_profit_pt,
            }
