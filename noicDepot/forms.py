from django import forms
from .models import Collections


class CollectionsForm(forms.ModelForm):
    class Meta:

        transporter = forms.CharField()
        truck_reg = forms.CharField()
        trailer_reg = forms.CharField()
        driver = forms.CharField()
        driver_id = forms.CharField()

        model = Collections
        fields = ['transporter', 'truck_reg', 'trailer_reg', 'driver', 'driver_id']

