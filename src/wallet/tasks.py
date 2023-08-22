from bender.celery_entry import app
from django.conf import settings
from django.contrib import admin, messages
from django.http.response import HttpResponseRedirect
from django.urls import path, reverse

from core.clients.binance import BinanceClient

from .models import Coin


@app.task(bind=True)
def debug_task(self):
    res = 'I`m OK'
    print(res)
    return res


@app.task(bind=True)
def task_get_coins(self):
    client = BinanceClient(settings.BINANCE_CLIENT)
    result, is_ok = client.get_coins()

    if not is_ok:
        return result

    i = 0
    for item in result:
        Coin.objects.update_or_create(
            coin=item['coin'],
            defaults={
                'deposit_all_enable': item['depositAllEnable'],
                'free': item['free'],
                'freeze': item['freeze'],
                'ipoable': item['ipoable'],
                'ipoing': item['ipoing'],
                'is_legal_money': item['isLegalMoney'],
                'locked': item['locked'],
                'name': item['name'],
                'storage': item['storage'],
                'trading': item['trading'],
                'withdraw_all_enable': item['withdrawAllEnable'],
                'withdrawing': item['withdrawing'],
            },
        )
        i += 1

    return {'result': f'Обновлено {i} записей.'}
