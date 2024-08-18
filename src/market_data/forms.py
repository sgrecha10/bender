from django import forms
from .models import ExchangeInfo


class MiddlePageForm(forms.Form):
    symbol = forms.ModelChoiceField(queryset=ExchangeInfo.objects.all(), label='Symbol')
    # interval = forms.ModelChoiceField(queryset=ExchangeInfo.objects.all(), label='Interval')
