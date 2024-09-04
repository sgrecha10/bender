import datetime

import pytz
from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime

from .models import ExchangeInfo, Interval, Kline


class DateTimeField(forms.DateTimeField):
    """Для работы widget AdminSplitDateTime"""
    def to_python(self, value):
        if isinstance(value, list):
            try:
                string_value = ' '.join(value)
                datetime_value = datetime.datetime.strptime(string_value, '%d.%m.%Y %H:%M')
                return datetime_value.replace(tzinfo=pytz.UTC)
            except (ValueError, TypeError):
                return
        return value


class GetKlineForm(forms.Form):
    symbol = forms.ModelChoiceField(
        queryset=ExchangeInfo.objects.all(),
        label='Symbol',
        initial='BTCUSDT',
    )
    interval = forms.ModelChoiceField(
        queryset=Interval.objects.all(),
        label='Interval',
        initial='1m',
    )
    start_time = DateTimeField(
        label='Start Time',
        widget=AdminSplitDateTime(),
        required=False,
    )
    end_time = DateTimeField(
        label='End Time',
        widget=AdminSplitDateTime(),
        required=False,
    )
    limit = forms.IntegerField(
        label='Limit',
        initial=1000,
    )


ALLOWED_INTERVAL = [
    'MINUTE_1',
    'HOUR_1',
    'DAY_1',
    'MONTH_1',
    'YEAR_1',
]


class ChartForm(forms.Form):
    symbol = forms.ModelChoiceField(
        queryset=ExchangeInfo.objects.filter(
            pk__in=list(Kline.objects.values_list('symbol', flat=True).distinct('symbol'))),
        label='Symbol',
    )
    interval = forms.ModelChoiceField(
        queryset=Interval.objects.filter(codename__in=ALLOWED_INTERVAL),
        label='Interval',
    )
    start_time = DateTimeField(
        label='Start Time',
        widget=AdminSplitDateTime(),
        required=False,
    )
    end_time = DateTimeField(
        label='End Time',
        widget=AdminSplitDateTime(),
        required=False,
    )
