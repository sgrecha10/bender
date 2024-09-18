import datetime

import pytz
from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime

from .constants import Interval, AllowedInterval
from .models import ExchangeInfo, Kline
from django.contrib.admin import widgets
from indicators.models import MovingAverage
from django.contrib import admin


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
    interval = forms.ChoiceField(
        choices=Interval.choices,
        label='Interval',
        initial=Interval.MINUTE_1,
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


# class Rel:
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.model = ExchangeInfo
#         self.limit_choices_to = 10
#
#     def get_related_field(self):
#         return ExchangeInfo._meta.get_field('symbol')


class ChartForm(forms.Form):
    symbol = forms.ModelChoiceField(
        queryset=ExchangeInfo.objects.all(),
        label='Symbol',
        # widget=widgets.ForeignKeyRawIdWidget(Rel(), admin.site),
    )
    interval = forms.ChoiceField(
        choices=AllowedInterval.choices,
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
    moving_average = forms.ModelChoiceField(
        queryset=MovingAverage.objects.all(),
        label='Moving Average',
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
