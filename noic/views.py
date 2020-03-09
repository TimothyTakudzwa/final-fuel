import secrets
from validate_email import validate_email
from datetime import datetime, timedelta

from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, update_session_auth_hash, login, logout
from datetime import datetime, date
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from itertools import chain
from operator import attrgetter

from buyer.models import User, FuelRequest
from company.models import Company, CompanyFuelUpdate
from supplier.models import Subsidiaries, SubsidiaryFuelUpdate, FuelAllocation, Transaction, Offer, DeliverySchedule
from fuelUpdates.models import SordCompanyAuditTrail
from users.models import SordActionsAuditTrail
from accounts.models import AccountHistory
from users.views import message_is_sent
from national.models import Order, NationalFuelUpdate

user = get_user_model()

# Create your views here.
def orders(request):
    orders = Order.objects.all()
    return render(request, 'noic/orders.html', {'orders': orders})

def dashboard(request):
    capacities = NationalFuelUpdate.objects.all()
    return render(request, 'noic/dashboard.html', {'capacities': capacities})


def allocations(request):
    return render(request, 'noic/allocations.html')

def rtgs_update(request, id):
    capacity = NationalFuelUpdate.objects.filter(id=id).first()
    if request.method == 'POST':
        if request.POST['fuel_type'].lower() == 'petrol':
            capacity.unallocated_petrol += float(request.POST['quantity'])
            capacity.petrol_price = request.POST['price']
            capacity.save()
            messages.success(request, 'updated petrol quantity successfully')
            return redirect('noic:dashboard')
            
        else:
            capacity.unallocated_diesel += float(request.POST['quantity'])
            capacity.diesel_price = request.POST['price']
            capacity.save()
            messages.success(request, 'updated diesel quantity successfully')
            return redirect('noic:dashboard')
    

def usd_update(request, id):
    capacity = NationalFuelUpdate.objects.filter(id=id).first()
    if request.method == 'POST':
        if request.POST['fuel_type'].lower() == 'petrol':
            capacity.unallocated_petrol += float(request.POST['quantity'])
            capacity.petrol_price = request.POST['price']
            capacity.save()
            messages.success(request, 'updated petrol quantity successfully')
            return redirect('noic:dashboard')
            
        else:
            capacity.unallocated_diesel += float(request.POST['quantity'])
            capacity.diesel_price = request.POST['price']
            capacity.save()
            messages.success(request, 'updated diesel quantity successfully')
            return redirect('noic:dashboard')

def edit_prices(request, id):
    capacity = NationalFuelUpdate.objects.filter(id=id).first()
    if request.method == 'POST':
        capacity.petrol_price = request.POST['petrol_price']
        capacity.diesel_price = request.POST['diesel_price']
        capacity.save()
        messages.success(request, 'updated prices successfully')
        return redirect('noic:dashboard')


def payment_approval(request, id):
    order = Order.objects.filter(id=id).first()
    order.payment_approved = True
    order.save()
    messages.success(request, 'payment approved successfully')
    return redirect('noic:orders')
            

def allocate_fuel(request, id):
    order = Order.objects.filter(id=id).first()
    if request.method == 'POST':
        if request.POST['fuel_type'].lower() == 'petrol':
            if request.POST['currency'] == 'USD':
                noic_capacity = NationalFuelUpdate.objects.filter(currency='USD').first()
                if request.POST['quantity'] > noic_capacity.unallocated_petrol:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_petrol}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_petrol -= float(request.POST['quantity'])
                    noic_capacity.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')
            
            else:
                noic_capacity = NationalFuelUpdate.objects.filter(currency='RTGS').first()
                if request.POST['quantity'] > noic_capacity.unallocated_petrol:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_petrol}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_petrol -= float(request.POST['quantity'])
                    noic_capacity.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')
            

        else:
            if request.POST['currency'] == 'USD':
                noic_capacity = NationalFuelUpdate.objects.filter(currency='USD').first()
                if request.POST['quantity'] > noic_capacity.unallocated_diesel:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_diesel}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')
            
            
            else:
                noic_capacity = NationalFuelUpdate.objects.filter(currency='RTGS').first()
                if request.POST['quantity'] > noic_capacity.unallocated_diesel:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_diesel}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')


def profile(request):
    user = request.user
    return render(request, 'noic/profile.html', {'user':user})