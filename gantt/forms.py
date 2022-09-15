from django import forms
from django.core.exceptions import ValidationError


class SimpleConfirm(forms.Form):
    confirm = forms.CharField(max_length=10)

    def clean_confirm(self):
        confirm_value = self.cleaned_data.get('confirm')
        if not (confirm_value and confirm_value == 'ok'):
            raise ValidationError(
                'not ok',
                code='phrase_mismatch',
            )
        return confirm_value
