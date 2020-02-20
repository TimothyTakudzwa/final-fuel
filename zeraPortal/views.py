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
from company.models import Company, CompanyFuelUpdate
from supplier.models import Subsidiaries, SubsidiaryFuelUpdate, FuelAllocation
user = get_user_model()



def dashboard(request):
    companies = Company.objects.filter(company_type='SUPPLIER').all()
    for company in companies:
        company.num_of_depots = Subsidiaries.objects.filter(company=company, is_depot='True').count()
        company.num_of_stations = Subsidiaries.objects.filter(company=company, is_depot='False').count()
    return render(request, 'zeraPortal/companies.html', {'companies': companies})

def company_fuel(request):
    capacities = CompanyFuelUpdate.objects.all()
    for fuel in capacities:
        subs_total_diesel_capacity = 0
        subs_total_petrol_capacity = 0
        subsidiaries_fuel = SubsidiaryFuelUpdate.objects.filter(subsidiary__company=fuel.company).all()
        for sub_fuel in subsidiaries_fuel:
            subs_total_diesel_capacity += sub_fuel.diesel_quantity
            subs_total_petrol_capacity += sub_fuel.petrol_quantity

        fuel.diesel_capacity = fuel.unallocated_diesel + subs_total_diesel_capacity
        fuel.petrol_capacity = fuel.unallocated_petrol + subs_total_petrol_capacity

        fuel.diesel_capacity = '{:,}'.format(fuel.diesel_capacity)
        fuel.petrol_capacity = '{:,}'.format(fuel.petrol_capacity)
    
    return render(request, 'zeraPortal/company_fuel.html', {'capacities': capacities})

def allocations(request, id):
    company = Company.objects.filter(id=id).first()
    allocations = FuelAllocation.objects.filter(company=company).all()
    for allocation in allocations:
        allocation.subsidiary = Subsidiaries.objects.filter(id=allocation.allocated_subsidiary_id).first()
    return render(request, 'zeraPortal/fuel_allocations.html', {'allocations': allocations, 'company': company})