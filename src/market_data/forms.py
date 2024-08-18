from django import forms
from .models import ExchangeInfo, Interval


class MiddlePageForm(forms.Form):
    symbol = forms.ModelChoiceField(
        queryset=ExchangeInfo.objects.all(),
        label='Symbol',
    )
    interval = forms.ModelChoiceField(
        queryset=Interval.objects.all(),
        label='Interval',
    )
    start_time = forms.DateTimeField(
        label='Start Time',
        # attrs={'class': 'form-control', 'type': 'date'}
        widget=forms.SplitDateTimeWidget(attrs={'class': 'form-control'}),
    )
    end_time = forms.DateTimeField(
        label='End Time',
    )
    limit = forms.IntegerField(
        label='Limit',
        initial=1000,
    )
