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
from users.forms import DepotContactForm
from company.models import Company, CompanyFuelUpdate
from supplier.models import Subsidiaries, SubsidiaryFuelUpdate, FuelAllocation, Transaction, Offer, DeliverySchedule
from fuelUpdates.models import SordCompanyAuditTrail
from users.models import SordActionsAuditTrail
from accounts.models import AccountHistory
from users.views import message_is_sent
from national.models import Order, NationalFuelUpdate, SordNationalAuditTrail, DepotFuelUpdate, NoicDepot

user = get_user_model()


# Create your views here.
def dashboard(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    orders = SordNationalAuditTrail.objects.filter(assigned_depot=depot).all()
    return render(request, 'noicDepot/dashboard.html', {'orders': orders})

def orders(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    orders = Order.objects.filter(noic_depot=depot).all()
    # form1 = DepotContactForm()
    # depots = NoicDepot.objects.all()
    # form1.fields['depot'].choices = [((depot.id, depot.name)) for depot in depots]

    return render(request, 'noic/orders.html', {'orders': orders})

def stock(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    depot_stock = DepotFuelUpdate.objects.filter(depot=depot).all()
    return render(request, 'noicDepot/stock.html', {'depot_stock': depot_stock, 'depot': depot})


def upload_release_note(request, id):
    allocation = SordNationalAuditTrail.objects.filter(id=id).first()
    if request.method == 'POST':
        allocation.release_date = request.POST['release_date']
        allocation.release_note = True
        allocation.save()
        messages.success(request, "Release Note Successfully created")
        return redirect('noicDepot:dashboard')


def view_release_note(request, id):
    allocation = SordNationalAuditTrail.objects.filter(id=id).first()
    allocation.admin = User.objects.filter(company=allocation.company).filter(user_type='S_ADMIN').first()
    allocation.rep = request.user
    context = {
        'allocation': allocation
    }
    return render(request, 'noicDepot/release_note.html', context=context)


def allocate_fuel(request, id):
    order = Order.objects.filter(id=id).first()
   
    if request.method == 'POST':
        if request.POST['fuel_type'].lower() == 'petrol':
            if request.POST['currency'] == 'USD':
                depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
                noic_capacity = DepotFuelUpdate.objects.filter(depot=depot).first()
                if float(request.POST['quantity']) > noic_capacity.usd_petrol:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.usd_petrol}L')
                    return redirect('noicDepot:orders')
                else:
                    noic_capacity.usd_petrol -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.usd_petrol_price = noic_capacity.usd_petrol_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noicDepot:orders')
            
            else:
                depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
                noic_capacity = DepotFuelUpdate.objects.filter(depot=depot).first()
                if float(request.POST['quantity']) > noic_capacity.rtgs_petrol:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.rtgs_petrol}L')
                    return redirect('noicDepot:orders')
                else:
                    noic_capacity.rtgs_petrol -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.petrol_price = noic_capacity.rtgs_petrol_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noicDepot:orders')
            

        else:
            if request.POST['currency'] == 'USD':
                depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
                noic_capacity = DepotFuelUpdate.objects.filter(depot=depot).first()
                if float(request.POST['quantity']) > noic_capacity.usd_diesel:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.usd_diesel}L')
                    return redirect('noicDepot:orders')
                else:
                    noic_capacity.usd_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.usd_diesel_price = noic_capacity.usd_diesel_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noicDepot:orders')
            
            
            else:
                depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
                noic_capacity = DepotFuelUpdate.objects.filter(depot=depot).first()
                if float(request.POST['quantity']) > noic_capacity.rtgs_diesel:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.rtgs_diesel}L')
                    return redirect('noicDepot:orders')
                else:
                    noic_capacity.rtgs_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.diesel_price = noic_capacity.rtgs_diesel_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noicDepot:orders')

def profile(request):
    user = request.user
    return render(request, 'noicDepot/profile.html', {'user': user})
