from django import forms
from .models import Notification


class NotificationForm(forms.ModelForm):
    class Meta:
        message = forms.Textarea
        fields = ['message']

