from django import forms
from buyer.models import User


class ZeraProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField()
    last_name = forms.CharField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']


class ZeraImageUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['image']
