import datetime

import pytz
from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime

from .models import ExchangeInfo, Interval, Kline
import market_data.constants as const


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


class ChartForm(forms.Form):
    ALLOWED_INTERVAL = [
        const.MINUTE_1,
        const.HOUR_1,
        const.DAY_1,
        const.MONTH_1,
        const.YEAR_1,
    ]

    symbol = forms.ModelChoiceField(
        queryset=ExchangeInfo.objects.all(),
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

    def clean(self):
        cleaned_data = super(ChartForm, self).clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time and end_time and end_time <= start_time:
            self.add_error('start_time', 'Incorrect dates, end_time <= start_time')

        symbol = cleaned_data.get('symbol')
        if not Kline.objects.filter(symbol=symbol).exists():
            self.add_error('symbol', 'Data not found')
