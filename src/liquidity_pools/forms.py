import re

from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from django.core.exceptions import ValidationError
from django.forms import SplitDateTimeField
from eth_account import Account

from .models import WalletAddress, LiquidityPool
from .services.cryptography_service import CryptographyService


class WalletAdminForm(forms.ModelForm):
    private_key = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'vTextField',
                'style': 'width: 100%; max-width: 700px;',
                'autocomplete': 'off',
                'autocapitalize': 'off',
                'autocorrect': 'off',
                'spellcheck': 'false',
                'data-lpignore': 'true',
                'name': 'wallet_private_key_input',
            }
        )
    )

    class Meta:
        model = WalletAddress
        fields = '__all__'

    def clean_private_key(self):
        key = self.cleaned_data['private_key'].strip()

        if not key:
            return None

        if key.startswith('0x'):
            key = key[2:]

        if not re.fullmatch(r'[0-9a-fA-F]{64}', key):
            raise ValidationError('Invalid format')

        try:
            Account.from_key(key)
        except Exception:
            raise ValidationError('Invalid private key')

        return key


    def save(self, commit=True):
        instance = super().save(commit=False)

        private_key = self.cleaned_data['private_key']

        if private_key:
            instance.encrypted_private_key = CryptographyService.encrypt_private_key(
                private_key=private_key,
            )
            instance.address = Account.from_key(
                private_key=private_key,
            ).address

        if commit:
            instance.save()

        return instance


class LiquidityPoolTickForm(forms.Form):
    liquidity_pool = forms.ModelChoiceField(
        queryset=LiquidityPool.objects.all(),
        label='Liquidity Pool',
    )
    start_datetime = SplitDateTimeField(widget=AdminSplitDateTime())
    end_datetime = SplitDateTimeField(widget=AdminSplitDateTime())
    interval_minutes = forms.IntegerField(
        initial=5,
        min_value=1,
    )
