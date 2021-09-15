from django import forms

from .models import Amount


class AmountCreationForm(forms.ModelForm):
    amount = forms.DecimalField(decimal_places=2, localize=True)

    class Meta:
        model = Amount
        fields = ('recipe', 'ingredient', 'amount')

    def save(self, commit=True):
        amount = super().save(commit=False)
        if commit:
            amount.save()
        return amount


class AmountChangeForm(forms.ModelForm):
    amount = forms.DecimalField(decimal_places=2, localize=True)

    class Meta:
        model = Amount
        fields = ('recipe', 'ingredient', 'amount')
