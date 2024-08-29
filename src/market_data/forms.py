import datetime

from django import forms
from .models import ExchangeInfo, Interval, Kline
from django.contrib.admin.widgets import AdminDateWidget, AdminTimeWidget, AdminSplitDateTime
import pytz


class DateTimeField(forms.DateTimeField):
    """Для работы widget AdminSplitDateTime"""
    def to_python(self, value):
        if isinstance(value, list):
            try:
                string_value = ' '.join(value)
                datetime_value = datetime.datetime.strptime(string_value, '%d.%m.%Y %H:%M')
                return datetime_value.replace(tzinfo=pytz.UTC)
            except ValueError:
                return
        return value


class GetKlineForm(forms.Form):
    symbol = forms.ModelChoiceField(
        queryset=ExchangeInfo.objects.all(),
        label='Symbol',
        initial=ExchangeInfo.objects.get(symbol='BTCUSDT'),
    )
    interval = forms.ModelChoiceField(
        queryset=Interval.objects.all(),
        label='Interval',
        initial=Interval.objects.get(codename='MINUTE_1'),
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
