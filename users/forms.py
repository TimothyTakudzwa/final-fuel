from datetime import timedelta, date

from django import forms
#from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import *
from supplier.models import *
from django.contrib.auth.models import User
from users.models import *

from .utils import *
from .widgets.select_time_widget import *


def validate_user_email(value):
    safe = True
    if '@' in value:
        if User.objects.filter(email=value.strip()).exists():
            safe = False
    if not safe:
        raise ValidationError('%(value)s is already registered',
            params={'value': value},)


class ReportForm(forms.Form):
    CHOICES = (('Transactions', 'Transactions'),('Fuel Requests', 'Fuel Requests'), ('Allocations', 'Allocations'))
    report_choices = forms.ChoiceField(choices=CHOICES)
    report_type = forms.ChoiceField(choices=CHOICES)
    start_date = forms.DateField(widget=forms.SelectDateWidget())
    end_date = forms.DateField(widget=forms.SelectDateWidget())


class BuyerContactForm(forms.Form):
    first_name = forms.CharField(label='First Name(s)', required=True,
                                max_length=30)
    last_name = forms.CharField(label='Last Name(s)', required=True,
                                 max_length=30)
    email = forms.EmailField(required=True, max_length=100,
                            validators=[validate_user_email])
    cellphone = forms.CharField(label='Cellphone number', required=True,
                                 max_length=100)
    telephone = forms.CharField(label='Telephone number', max_length=100,
                                required=False)
    password = forms.CharField(label='Password', required=True, max_length=100,
                             widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password Confirm', required=True,
                             widget=forms.PasswordInput, max_length=100)

    def clean(self):
        cleaned_data = super(BuyerContactForm, self).clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password != password2:
            raise forms.ValidationError("The passwords do not match!")

FUEL_CHOICES=[('Petrol', 'PETROL'), ('Diesel', 'DIESEL'),]
class AllocationForm(forms.Form):
    service_station = forms.ChoiceField()
    fuel_type = forms.ChoiceField(choices=FUEL_CHOICES)
    quantity = forms.CharField(label='Quantity', required=True)
    staff = forms.ChoiceField()

class ApplicantContactForm(forms.Form):
    choice=(('Soccer','Soccer'),('Bibo','Bibo'))
    service_station = forms.ChoiceField()
    depot = forms.ChoiceField()
    sports = forms.ChoiceField(label='Sports', choices=choice)

def approve_staf(request):
    return {
        'approve_form': ApplicantContactForm()
    }    
class SupplierContactForm(forms.Form):
    first_name = forms.CharField(label='First Name', required=True,
                                 max_length=30)  
    last_name = forms.CharField(label='Last Name', required=True,
                                 max_length=30)                         
    service_station = forms.ChoiceField()
    email = forms.EmailField(required=True, max_length=100,
                            validators=[validate_user_email])
    phone_number = forms.CharField(label='Cellphone number', required=True,
                                 max_length=100)

    def clean(self):
        cleaned_data = super(SupplierContactForm, self).clean()
        

class DepotContactForm(forms.Form):
    first_name = forms.CharField(label='First Name', required=True,
                                 max_length=30)  
    last_name = forms.CharField(label='Last Name', required=True,
                                 max_length=30)                         
    depot = forms.ChoiceField()
    email = forms.EmailField(required=True, max_length=100,
                            validators=[validate_user_email])
    phone_number = forms.CharField(label='Cellphone number', required=True,
                                 max_length=100)
    

    def clean(self):
        cleaned_data = super(DepotContactForm, self).clean()
        


class SupplierProfileEditForm(forms.Form):
    name = forms.CharField(label='Name(s)', required=True,
                                max_length=30)
   
    phone = forms.CharField(label='Phone', required=True,
                                max_length=30)
    street = forms.CharField(label='Street', required=True,
                                max_length=30)
    city = forms.CharField(label='City', required=True,
                                max_length=30)
   
class ProfileEditForm(forms.Form):
    name = forms.CharField(label='Name(s)', required=True,
                                max_length=30)
    phone = forms.CharField(label='Phone', required=True,
                                max_length=30)
    
class ActionForm(forms.Form):
    pass                    


class UsersUploadForm(forms.Form):
    file = forms.FileField(required=True)
