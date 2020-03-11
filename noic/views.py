import secrets
from validate_email import validate_email
from datetime import datetime, timedelta, date

from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, update_session_auth_hash, login, logout
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

from .lib import *

user = get_user_model()

# Create your views here.
def orders(request):
    orders = Order.objects.all()
    form1 = DepotContactForm()
    depots = NoicDepot.objects.all()
    form1.fields['depot'].choices = [((depot.id, depot.name)) for depot in depots]

    return render(request, 'noic/orders.html', {'orders': orders, 'form1': form1})

def dashboard(request):
    capacities = NationalFuelUpdate.objects.all()
    depots = DepotFuelUpdate.objects.all()
    return render(request, 'noic/dashboard.html', {'capacities': capacities, 'depots': depots})


def allocations(request):
    allocations = SordNationalAuditTrail.objects.all()
    return render(request, 'noic/allocations.html', {'allocations': allocations})

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
                if float(request.POST['quantity']) > noic_capacity.unallocated_petrol:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_petrol}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_petrol -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.usd_petrol_price = noic_capacity.petrol_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')
            
            else:
                noic_capacity = NationalFuelUpdate.objects.filter(currency='RTGS').first()
                if float(request.POST['quantity']) > noic_capacity.unallocated_petrol:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_petrol}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_petrol -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.petrol_price = noic_capacity.petrol_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')
            

        else:
            if request.POST['currency'] == 'USD':
                noic_capacity = NationalFuelUpdate.objects.filter(currency='USD').first()
                if float(request.POST['quantity']) > noic_capacity.unallocated_diesel:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_diesel}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.usd_diesel_price = noic_capacity.diesel_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')
            
            
            else:
                noic_capacity = NationalFuelUpdate.objects.filter(currency='RTGS').first()
                if float(request.POST['quantity']) > noic_capacity.unallocated_diesel:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_diesel}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.diesel_price = noic_capacity.diesel_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')


def statistics(request):
    return render(request, 'noic/statistics.html')


def report_generator(request):

    '''View to dynamically render form tables based on different criteria'''
    allocations = requests = orders = stock = None
    # orders = Transaction.objects.filter(supplier__company=request.user.company).all()
    start_date = start = "December 1 2019"
    end_date = end = "January 1 2019"

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            start_date = start_date.date()
        report_type = request.POST.get('report_type')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date.date()
        if request.POST.get('report_type') == 'Stock':
            stock = CompanyFuelUpdate.objects.filter(company=request.user.company).all()

            requests = None
            allocations = None
            orders = None
            revs = None
            verified_companies=None
            unverified_companies=None
        if request.POST.get('report_type') == 'Orders':
            orders = Order.objects.filter(date__range=[start_date, end_date])
            print('I am in orders')
            requests = None
            allocations = None
            revs = None
            verified_companies=None
            unverified_companies=None
        if request.POST.get('report_type') == 'Requests':
            requests = FuelRequest.objects.filter(date__range=[start_date, end_date])
            print(f'__________________{requests}__________________________________')
            orders = None
            allocations = None
            stock = None
            revs = None
            verified_companies=None
            unverified_companies=None
        if request.POST.get('report_type') == 'Companies - Verified':
            v_companies = Company.objects.filter(is_verified=True)
            verified_companies = []

            for company in v_companies:
                company.admin = User.objects.filter(company=company).first()
                verified_companies.append(company)


            print(f'__________________{verified_companies}__________________________________')
            orders = None
            allocations = None
            stock = None
            revs = None
            unverified_companies=None
        if request.POST.get('report_type') == 'Companies - Unverified':
            uv_companies = Company.objects.filter(is_verified=False)
            unverified_companies = []

            for company in uv_companies:
                company.admin = User.objects.filter(company=company).first()
                unverified_companies.append(company)


            print(f'__________________{unverified_companies}__________________________________')
            orders = None
            allocations = None
            stock = None
            revs = None
            verified_companies=None
        if request.POST.get('report_type') == 'Allocations':
            print("__________________________I am in allocations____________________________")
            allocations = NationalFuelUpdate.objects.all()
            print(f'________________________________{allocations}__________________________')
            requests = None
            revs = None
            stock = None
            verified_companies=None
            unverified_companies=None
        start = start_date
        end = end_date
    return render(request, 'noic/reports.html')


def profile(request):
    user = request.user
    return render(request, 'noic/profile.html', {'user':user})


def report_generator(request):
    '''View to dynamically render form tables based on different criteria'''
    orders = pending_orders = complete_orders = stock = allocations_per_supplier = None

    # orders = Transaction.objects.filter(supplier__company=request.user.company).all()
    start_date = start = "December 1 2019"
    end_date = end = "January 1 2019"

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            start_date = start_date.date()
        report_type = request.POST.get('report_type')
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date.date()
        if request.POST.get('report_type') == 'Stock':
            stock = type('test', (object,), {})()
            stock.date = datetime.datetime.today()
            stock.usd, stock.zwl = get_current_usd_stock(), get_current_zwl_stock()

            allocations_per_supplier = None
            pending_orders = None
            orders = None
            complete_orders = None    

        if request.POST.get('report_type') == 'Pending Orders':
            pending_orders = Order.objects.filter(date__range=[start_date, end_date],
                                               payment_approved=False)
            stock = None
            allocations_per_supplier = None
            orders = None
            complete_orders = None    

        if request.POST.get('report_type') == 'All Orders':
            orders = Order.objects.filter(date__range=[start_date, end_date])
            print(f'__________________{orders}__________________________________')
            print(f'__________________I am in Orders__________________________________')

            pending_orders = None
            allocations_per_supplier = None
            stock = None
            complete_orders = None    

        if request.POST.get('report_type') == 'Completed Orders':
            complete_orders = Order.objects.filter(date__range=[start_date, end_date], payment_approved=True)
            print(f'__________________{complete_orders}__________________________________')
            print(f'__________________I am in complete_orders__________________________________')

            pending_orders = None
            allocations_per_supplier = None
            stock = None
            orders = None    
        if request.POST.get('report_type') == 'Allocations Per Supplier':
            print("__________________________I am in allocations per supplier____________________________")
            allocations = FuelAllocation.objects.all()
            supplier_allocations = User.objects.filter(user_type='S_ADMIN')
            allocations_per_supplier=[]
            for supplier in allocations:
                order_count = 0
                order_quantity = 0
                for order in SordNationalAuditTrail.objects.filter(company=supplier.company):
                    order_count += 1
                    order_quantity += order.quantity
                supplier.order_count = order_count
                supplier.order_quantity = order_quantity
                if supplier not in allocations_per_supplier:
                    allocations_per_supplier.append(supplier)      

            print(f'________________________________{allocations_per_supplier}__________________________')
            pending_orders = None
            orders = None
            complete_orders = None    
            stock = None
        start = start_date
        end = end_date

        # revs = 0
        return render(request, 'noic/reports.html',
                      {'orders': orders, 'pending_orders': pending_orders, 'complete_orders': complete_orders,
                       'start': start, 'end': end, 'stock': stock, 'allocations_per_supplier':allocations_per_supplier})

    show = False
    return render(request, 'noic/reports.html',
                  {'orders': orders, 'pending_orders': pending_orders, 'complete_orders': complete_orders,
                       'start': start, 'end': end, 'stock': stock})

# @login_required()
def statistics(request):
    unallocated_diesel = get_current_stock()[0]
    unallocated_petrol = get_current_stock()[1]
    total_allocations_quantity = get_total_allocations()
    orders_complete_percentage = get_complete_orders_percentage
    orders_this_week_count = orders_made_this_week() 
    orders_number = total_orders()
    monthly_rev = get_monthly_orders()

    fuel_orders = Order.objects.filter(payment_approved=True).annotate(
        number_of_orders=Count('company')).order_by('-number_of_orders')
    all_clients = [order.company for order in fuel_orders]

    all_clients = []
    for client in all_clients:
        total_transactions = all_clients.count(client)
        all_clients.remove(client)
        new_client_orders = Order.objects.filter(company=client, payment_approved=True).all()
        total_value = 0
        total_client_orders = []
        number_of_orders = 0
        for tran in new_client_orders:
            total_value += (tran.quantity)
            total_client_orders.append(tran)
            number_of_orders += 1
        client.total_revenue = total_value
        client.total_client_orders = total_client_orders
        client.number_of_orders = total_transactions
        if client not in all_clients:
            all_clients.append(clieny)

    clients = sorted(all_clients, key=lambda x: x.total_revenue, reverse=True)
    
    return render(request, 'noic/statistics.html', {'unallocated_diesel':unallocated_diesel,'unallocated_petrol': unallocated_petrol,
                            'total_allocations_quantity':total_allocations_quantity, 'orders_complete_percentage': orders_complete_percentage,
                            'orders_this_week_count':orders_this_week_count, 'orders_number':orders_number, 'monthly_rev': monthly_rev,
                             'clients':clients})
