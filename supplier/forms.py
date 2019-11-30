from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import  FuelRequest
from company.models import Company
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import  FuelRequest, Offer
from company.models import Company, FuelUpdate

User = get_user_model()
FUEL_CHOICES=[('PETROL', 'PETROL'), ('DIESEL', 'DIESEL'),]
STATUS_CHOICES = (('OPEN','open'),('CLOSED','Closed'),('OFFLOADING','Offloading'))
PAYING_CHOICES = (('USD', 'USD'),('TRANSFER','TRANSFER'),('BOND CASH','BOND CASH'),('USD & TRANSFER','USD & TRANSFER'),('TRANSFER & BOND CASH','TRANSFER & BOND CASH'),('USD & BOND CASH','USD & BOND CASH'),('USD, TRANSFER & BOND CASH','USD, TRANSFER & BOND CASH'))

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


# class RegistrationProfileForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ['phone']


class RegistrationEmailForm(forms.Form):
    email = forms.EmailField()


class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField()
    last_name = forms.CharField()
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']


# class ProfileUpdateForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ['phone']


# class ProfilePictureUpdateForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ['picture']


class FuelRequestForm(forms.ModelForm):
    OPTIONS= [
    ('SELF COLLECTION', 'SELF COLLECTION'),
    ('DELIVERY', 'DELIVERY'),
    ]

    delivery_method = forms.CharField(label='Delivery Method', widget=forms.Select(choices=OPTIONS))
    
    class Meta:
        model = FuelRequest
        fields = ['amount',  'payment_method', 'delivery_method', 'fuel_type']
        

class FuelUpdateForm(forms.ModelForm):
    OPTIONS= [
    ('PETROL', 'Petrol'),
    ('DIESEL', 'Diesel'),
    ('BLEND', 'Blend'),
    ]

    fuel_type = forms.CharField(label='Fuel Type', widget=forms.Select(choices=OPTIONS))
    payment_method = forms.CharField(label='Payment Method', widget=forms.Select(choices=PAYING_CHOICES))



class QuantityLevelForm(forms.Form):
    petrol_quantity = forms.CharField(label='Petrol Quantity')
    petrol_price = forms.CharField(label='Petrol Price')
    diesel_quantity = forms.CharField(label='Diesel Quantity')
    diesel_price = forms.CharField(label='Diesel Price')
    payment_methods = forms.CharField(label='Payment Method', widget=forms.Select(choices=PAYING_CHOICES))
    queue_length = forms.CharField(label='Queue Length', widget=forms.Select(choices=(('short', 'Short'), ('medium', 'Medium Long'), ('long', 'Long'))))


def fuelupdating(request):
    return {
        'update_form': QuantityLevelForm()
    }

class StockLevelForm(forms.Form):
    sub_type = forms.CharField(label='Subsisdiary Type', widget=forms.Select(choices=(('service_station', 'Service Station'), ('depot', 'Depot'),('company', 'Company'))))
    petrol_quantity = forms.CharField(label='Petrol Quantity')
    petrol_price = forms.CharField(label='Petrol Price')
    diesel_quantity = forms.CharField(label='Diesel Quantity')
    diesel_price = forms.CharField(label='Diesel Price')
    payment_methods = forms.CharField(label='Payment Method', widget=forms.Select(choices=PAYING_CHOICES))
    queue_length = forms.CharField(label='Queue Length', widget=forms.Select(choices=(('short', 'Short'), ('medium', 'Medium Long'), ('long', 'Long'))))

    #class Meta:
       # model = FuelUpdate
        #fields = [ 'petrol_quantity']

class SubsidiaryForm(forms.Form):
    name = forms.CharField(label='Subsisdiary Name')
    address = forms.CharField(label='Subsisdiary Address')
    is_depot = forms.CharField(label='Is Depot',  widget=forms.Select(choices=((True,True),(False,False))))
    opening_time = forms.CharField(label='Opening Time')
    closing_time = forms.CharField(label='Closing Time')
    
def create_sub(request):
    return {
        'sub_create_form': SubsidiaryForm()
    }

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