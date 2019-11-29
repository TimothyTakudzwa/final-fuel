from datetime import timedelta, date

from django import forms
#from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from django.contrib.auth.models import User

from .utils import *

class ProfileUdateForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.CharField(max_length=100, required=True)
    phone_number = forms.CharField(max_length=100, required=True)
    service_station = forms.CharField(max_length=200, required = True)

