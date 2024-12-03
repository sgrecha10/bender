from django import forms
from django.contrib import messages

from indicators.models import StandardDeviation


class StandardDeviationForm(forms.ModelForm):
    class Meta:
        model = StandardDeviation
        fields = '__all__'

    def clean(self):
        cleaned_data = super(StandardDeviationForm, self).clean()

        if cleaned_data['kline_count'] > cleaned_data['moving_average'].kline_count:
            messages.warning(self.request, 'kline_count larger than moving_average.kline_count')

        return cleaned_data
