from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Profile, FuelUpdate, FuelRequest
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import Profile, FuelUpdate, FuelRequest, Offer
from buyer.constants import *

User = get_user_model()
FUEL_CHOICES=[('PETROL', 'PETROL'), ('DIESEL', 'DIESEL'),]
STATUS_CHOICES = (('OPEN','open'),('CLOSED','Closed'),('OFFLOADING','Offloading'))

class PasswordChange(PasswordChangeForm):
    class Meta:
        widgets = {

        }
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']


class RegistrationForm(UserCreationForm):
    class Meta:
        widgets = {
            'password': forms.PasswordInput()
        }

        model = User
        fields = ['username', 'password1', 'password2']


class RegistrationProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone']


class RegistrationEmailForm(forms.Form):
    email = forms.EmailField()


class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField()
    last_name = forms.CharField()
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone']


class ProfilePictureUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['picture']


class FuelRequestForm(forms.ModelForm):
    OPTIONS= [
    ('SELF COLLECTION', 'SELF COLLECTION'),
    ('DELIVERY', 'DELIVERY'),
    ]

    delivery_method = forms.CharField(label='Delivery Method', widget=forms.Select(choices=OPTIONS))
    
    class Meta:
        model = FuelRequest
        fields = ['amount', 'split', 'payment_method', 'delivery_method', 'fuel_type']
        

class FuelUpdateForm(forms.ModelForm):
    OPTIONS= [
    ('PETROL', 'Petrol'),
    ('DIESEL', 'Diesel'),
    ('BLEND', 'Blend'),
    ]

    fuel_type = forms.CharField(label='Fuel Type', widget=forms.Select(choices=OPTIONS))
    payment_method = forms.CharField(label='Payment Method', widget=forms.Select(choices=PAYING_CHOICES))

    class Meta:
        model = FuelUpdate
        fields = ['fuel_type', 'available_quantity', 'price', 'payment_method', 'status', 'queue_size']


class StockLevelForm(forms.ModelForm):

    fuel_type = forms.CharField(label='Fuel Type', widget=forms.Select(choices=FUEL_CHOICES))
    status = forms.CharField(label='Status', widget=forms.Select(choices=STATUS_CHOICES))
    payment_method = forms.CharField(label='Payment Method', widget=forms.Select(choices=PAYING_CHOICES))

    class Meta:
        model = FuelUpdate
        fields = ['fuel_type', 'available_quantity', 'price','payment_method','status']



class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['quantity', 'price']

class EditOfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['quantity', 'price']


def fuelupdate(request):
    return {
        'fuel_update_form': StockLevelForm()
    }


def makeoffer(request):
    return {
        'make_offer_form': OfferForm()
    }

def editoffer(request):
    return {
        'edit_offer_form': EditOfferForm()
    }