from django import forms 
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,  PasswordChangeForm
from .models import  FuelRequest
from .constants import *
from django.contrib.auth import get_user_model

User = get_user_model()

OPTIONS= [
('BUYER', ' Corporate Buyer'),
('SUPPLIER', 'Fuel Supplier'),
]


class BuyerRegisterForm(forms.ModelForm):
    first_name = forms.CharField() 
    last_name = forms.CharField()
    email = forms.EmailField()
    phone_number = forms.CharField(initial=263)
    user_type = forms.CharField(label='User Type', widget=forms.Select(choices=OPTIONS))
    class Meta: 
        model = User
        fields = [ 'first_name', 'last_name', 'email', 'phone_number', 'user_type']

    def clean_email(self):
        data = self.cleaned_data['email']
        if User.objects.filter(email=data).count() > 0:
            raise forms.ValidationError("We have a user with this user email-id")
        return data
    


class SupplierUserForm(forms.Form):
    company = forms.CharField()
    phone_number = forms.CharField()
    supplier_role = forms.CharField()

class PasswordChange(PasswordChangeForm):
    class Meta:
    
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']

    
class BuyerUpdateForm(UserCreationForm):    
    class Meta:
        model = User   
        fields = ['image', 'password1', 'password2']

class FuelRequestForm(forms.ModelForm):

    delivery_method = forms.CharField(label='Delivery Method', widget=forms.Select(choices=DELIVERY_OPTIONS))
    fuel_type = forms.CharField(label='Fuel Type', widget=forms.Select(choices=FUEL_CHOICES))
    amount = forms.IntegerField(label='Quantity')
    storage_tanks = forms.CharField(label='Storage Tanks', widget=forms.Select(choices=STORAGE_TANKS))

    class Meta: 
        model = FuelRequest
        fields = ['fuel_type','amount', 'delivery_method','pump_required', 'dipping_stick_required']
