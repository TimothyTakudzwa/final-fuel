import secrets

from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, update_session_auth_hash, login, logout
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from itertools import chain
from operator import attrgetter

from buyer.models import User
from company.models import Company
from supplier.models import Subsidiaries
user = get_user_model()



def dashboard(request):
    companies = Company.objects.filter(company_type='SUPPLIER').all()
    for company in companies:
        company.num_of_depots = Subsidiaries.objects.filter(company=company, is_depot='True').count()
        company.num_of_stations = Subsidiaries.objects.filter(company=company, is_depot='False').count()
    return render(request, 'zeraPortal/companies.html', {'companies': companies})