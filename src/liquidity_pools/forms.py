import re

from django import forms
from django.core.exceptions import ValidationError
from eth_account import Account

from .models import WalletAddress
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
        fields = (
            'private_key',
            'chain_id',
            'label',
            'is_active',
        )

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
