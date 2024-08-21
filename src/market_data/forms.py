from django import forms
from .models import ExchangeInfo, Interval, Kline
from django.contrib.admin.widgets import AdminDateWidget, AdminTimeWidget, AdminSplitDateTime


class DateTimeField(forms.DateTimeField):
    def to_python(self, value):
        if isinstance(value, list):
            if [x for x in value if x is not None]:
                return ' '.join(value)
            return
        return value


class MiddlePageForm(forms.Form):
    symbol = forms.ModelChoiceField(
        queryset=ExchangeInfo.objects.all(),
        label='Symbol',
    )
    interval = forms.ModelChoiceField(
        queryset=Interval.objects.all(),
        label='Interval',
    )
    start_time = DateTimeField(
        label='Start Time',
        widget=AdminSplitDateTime(),
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
