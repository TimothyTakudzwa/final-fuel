from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import  FuelRequest
from company.models import Company
from django.contrib.auth import get_user_model
from supplier.models import Subsidiaries
from .constants import *
User = get_user_model()
from .models import  FuelRequest, Offer, DeliverySchedule
from .constants import Harare
# from company.models import Company, FuelUpdate
from buyer.constants2 import *
from buyer.constants import *

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

class CreateCompany(forms.ModelForm):
    company_name = forms.CharField(required=True)
    address = forms.CharField(required=True)
   

    class Meta:
        model = Company
        fields = ['company_name', 'address', 'logo']


class FuelRequestForm(forms.ModelForm):
    OPTIONS= [
    ('SELF COLLECTION', 'SELF COLLECTION'),
    ('DELIVERY', 'DELIVERY'),
    ]

    delivery_method = forms.CharField(label='Delivery Method', widget=forms.Select(choices=OPTIONS))
    
    class Meta:
        model = FuelRequest
        fields = ['amount', 'delivery_method', 'fuel_type']

class PostForm(forms.ModelForm):

    class Meta:
        model = Subsidiaries
        fields = ['logo']

class SubForm(forms.ModelForm):
    city = forms.CharField(label='City', widget=forms.Select(choices=Zimbabwean_Towns))

    class Meta:
        model = Subsidiaries
        fields = ['city','location']
        
        

class FuelUpdateForm(forms.ModelForm):
    OPTIONS= [
    ('PETROL', 'Petrol'),
    ('DIESEL', 'Diesel'),
    ('BLEND', 'Blend'),
    ]

    fuel_type = forms.CharField(label='Fuel Type', widget=forms.Select(choices=OPTIONS))



class QuantityLevel1Form(forms.Form):
    petrol_quantity = forms.CharField(label='Petrol Quantity')
    #diesel_quantity = forms.CharField(label='Diesel Quantity')
    cash = forms.CharField(label='Accepts Cash',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    usd = forms.CharField(label='Accepts USD ',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    swipe = forms.CharField(label='Accepts Swipe ',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    ecocash = forms.CharField(label='Accepts Ecocash ',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    


def fuelupdating1(request):
    return {
        'update_form': QuantityLevel1Form()
    }

class QuantityLevel2Form(forms.Form):
    #petrol_quantity = forms.CharField(label='Petrol Quantity')
    diesel_quantity = forms.CharField(label='Diesel Quantity')
    cash = forms.CharField(label='Accepts Cash',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    usd = forms.CharField(label='Accepts USD ',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    swipe = forms.CharField(label='Accepts Swipe ',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    ecocash = forms.CharField(label='Accepts Ecocash ',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    


def fuelupdating2(request):
    return {
        'updating_form': QuantityLevel2Form()
    }

class StockLevelForm(forms.Form):
    sub_type = forms.CharField(label='Subsisdiary Type', widget=forms.Select(choices=(('service_station', 'Service Station'), ('depot', 'Depot'),('company', 'Company'))))
    petrol_quantity = forms.CharField(label='Petrol Quantity')
    petrol_price = forms.CharField(label='Petrol Price')
    diesel_quantity = forms.CharField(label='Diesel Quantity')
    diesel_price = forms.CharField(label='Diesel Price')
    queue_length = forms.CharField(label='Queue Length', widget=forms.Select(choices=(('short', 'Short'), ('medium', 'Medium Long'), ('long', 'Long'))))

    #class Meta:
       # model = FuelUpdate
        #fields = [ 'petrol_quantity']

class SubsidiaryForm(forms.Form):
    
    name = forms.CharField(label='Subsisdiary Name')
    address = forms.CharField(label='Subsisdiary Address')
    is_depot = forms.CharField(label='Is Depot',  widget=forms.Select(choices=((True,True),(False,False))))   
    cash = forms.CharField(label='Accepts Cash',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    usd = forms.CharField(label='Accepts USD ',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    swipe = forms.CharField(label='Accepts Swipe ',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    ecocash = forms.CharField(label='Accepts Ecocash ',  widget=forms.Select(choices=((True,'Yes'),(False,"No"))))
    city = forms.CharField(label='City', widget=forms.Select(choices=Zimbabwean_Towns))
    location = forms.CharField(label='Location', widget=forms.Select(choices=Harare))
   

def create_sub(request):
    return {
        'sub_create_form': SubsidiaryForm()
    }

class OfferForm(forms.ModelForm):
    delivery_method = forms.CharField(label='Delivery Method', widget=forms.Select(choices=DELIVERY_OPTIONS))
    fuel_type = forms.CharField(label='Fuel Type', widget=forms.Select(choices=FUEL_CHOICES))
    quantity = forms.IntegerField(label='Quantity')

    class Meta: 
        model = Offer
        fields = ['fuel_type','quantity', 'delivery_method','pump_available', 'dipping_stick_available']

class EditOfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['quantity', 'price']


class StockForm(forms.Form):
    petrol_quantity = forms.CharField(label='Petrol Quantity')
    petrol_price = forms.CharField(label='Petrol Price')
    diesel_quantity = forms.CharField(label='Diesel Quantity')
    diesel_price = forms.CharField(label='Diesel Price')


def stock_form(request):
    return {
        'stock_form': StockForm()
    }



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

class DeliveryScheduleForm(forms.ModelForm):
    class Meta:
        models = DeliverySchedule
        fields = ['confirmation_document']