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
@login_required
def initial_password_change(request):
    if request.method == 'POST':
        password1 = request.POST['new_password1']
        password2 = request.POST['new_password2']
        if password1 != password2:
            messages.warning(request, "Passwords don't match")
            return redirect('noicDepot:initial-password-change')
        elif len(password1) < 8:
            messages.warning(request, "Password is too short")
            return redirect('noicDepot:initial-password-change')
        elif password1.isnumeric():
            messages.warning(request, "Password can not be entirely numeric!")
            return redirect('noicDepot:initial-password-change')
        elif not password1.isalnum():
            messages.warning(request, "Password should be alphanumeric")
            return redirect('noicDepot:initial-password-change')
        else:
            user = request.user
            user.set_password(password1)
            user.password_reset = False
            user.save()
            update_session_auth_hash(request, user)

            messages.success(request, 'Password successfully changed')
            return redirect('noicDepot:orders')
    return render(request, 'noicDepot/initial_pass_change.html')


def dashboard(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    orders = SordNationalAuditTrail.objects.filter(assigned_depot=depot).all()
    return render(request, 'noicDepot/dashboard.html', {'orders': orders})

def orders(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    orders = Order.objects.filter(noic_depot=depot).all()
    print(orders)
    for order in orders:
        if order is not None:
            alloc = SordNationalAuditTrail.objects.filter(order=order).first()
            if alloc is not None:
                order.allocation = alloc
    return render(request, 'noicDepot/orders.html', {'orders': orders})

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
        messages.success(request, "Release note successfully created")
        return redirect('noicDepot:dashboard')

def payment_approval(request, id):
    order = Order.objects.filter(id=id).first()
    order.payment_approved = True
    order.save()
    messages.success(request, 'payment approved successfully')
    return redirect('noicDepot:orders')

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
                    sord_object = SordNationalAuditTrail.objects.create(price=noic_capacity.usd_petrol_price, order=order, assigned_depot=depot, company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving from NOIC',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
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
                    sord_object = SordNationalAuditTrail.objects.create(price=noic_capacity.rtgs_petrol_price, order=order, assigned_depot=depot, company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
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
                    sord_object = SordNationalAuditTrail.objects.create(price=noic_capacity.usd_diesel_price, order=order, assigned_depot=depot, company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_diesel += float(request.POST['quantity'])
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
                    sord_object = SordNationalAuditTrail.objects.create(price=noic_capacity.rtgs_diesel_price, order=order, assigned_depot=depot, company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_diesel += float(request.POST['quantity'])
                    company_update.diesel_price = noic_capacity.rtgs_diesel_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noicDepot:orders')

def download_proof(request, id):
    order = Order.objects.filter(id=id).first()
    if order:
        filename = order.proof_of_payment.name.split('/')[-1]
        response = HttpResponse(order.proof_of_payment, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found')
        return redirect('noicDepot:orders')
    return response


def download_d_note(request, id):
    allocation = SordNationalAuditTrail.objects.filter(id=id).first()
    if allocation:
        filename = allocation.d_note.name.split('/')[-1]
        response = HttpResponse(allocation.d_note, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found')
        return redirect('noicDepot:dashboard')
    return response


def profile(request):
    user = request.user
    return render(request, 'noicDepot/profile.html', {'user': user})


def report_generator(request):
    '''View to dynamically render form tables based on different criteria'''
    allocations = requests = trans = stock = None
    # trans = Transaction.objects.filter(supplier__company=request.user.company).all()
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
            depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
            stock = DepotFuelUpdate.objects.filter(depot=depot).first()

            print('______________________{stock}_________________')
            print('______________________Im in stock_________________')



            allocations = None
            pending_orders = None
            orders = None
            complete_orders = None    

        if request.POST.get('report_type') == 'Pending Orders':
            depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
            pending_orders = Order.objects.filter(date__range=[start_date, end_date],
                                               payment_approved=False, noic_depot=depot)
            print(f'__________________{pending_orders}__________________________________')
            print(f'__________________I am in Pending Orders__________________________________')


            stock = None
            allocations = None
            orders = None
            complete_orders = None
        
        if request.POST.get('report_type') == 'Allocations':
            depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
            allocations = []
            if depot:
                allocations = SordNationalAuditTrail.objects.filter(assigned_depot=depot)
            # allocations = SordNationalAuditTrail.objects.all()
            print(f'__________________{allocations[0].price}__________________________________')
            print(f'__________________I am in Allocations ')


            stock = None
            orders = None
            complete_orders = None       
            pending_orders = None


        if request.POST.get('report_type') == 'All Orders':
            depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
            orders = Order.objects.filter(date__range=[start_date, end_date], noic_depot=depot)
            print(f'__________________{orders}__________________________________')
            print(f'__________________I am in Orders__________________________________')

            pending_orders = None
            allocations = None
            stock = None
            complete_orders = None    

        if request.POST.get('report_type') == 'Completed Orders':
            depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
            complete_orders = Order.objects.filter(date__range=[start_date, end_date], payment_approved=True, noic_depot=depot)
            print(f'__________________{complete_orders}__________________________________')
            print(f'__________________I am in complete_orders__________________________________')

            pending_orders = None
            allocations = None
            stock = None
            orders = None    
        if request.POST.get('report_type') == 'Allocations Per Supplier':
            print("__________________________I am in allocations per supplier____________________________")
            allocations = FuelAllocation.objects.all()
            supplier_allocations = User.objects.filter(user_type='S_ADMIN')
            allocations = []
            for supplier in supplier_allocations:
                order_count = 0
                order_quantity = 0
                for order in SordNationalAuditTrail.objects.filter(company=supplier.company):
                    order_count += 1
                    order_quantity += order.quantity
                supplier.order_count = order_count
                supplier.order_quantity = order_quantity
                if supplier not in allocations:
                    allocations.append(supplier) 

            print(f'________________________________{allocations}__________________________')
            pending_orders = None
            orders = None
            complete_orders = None    
            stock = None
        start = start_date
        end = end_date

        # revs = 0
        return render(request, 'noicDepot/reports.html',
                      {'trans': trans, 'requests': requests, 'allocations': allocations, 'orders':orders,
                       'complete_orders':complete_orders,'pending_orders': pending_orders,'start': start, 'end': end, 'stock': stock})

    show = False
    print(trans)
    return render(request, 'noicDepot/reports.html',
                  {'trans': trans, 'requests': requests, 'allocations': allocations,
                   'start': start_date, 'end': end_date, 'show': show, 'stock': stock})


def statistics(request):
    # yesterday = date.today() - timedelta(days=1)
    # monthly_rev = get_aggregate_monthly_sales(datetime.now().year)
    # weekly_rev = get_weekly_sales(True)
    # last_week_rev = get_weekly_sales(False)
    # city_sales_volume = get_volume_sales_by_location()
    # final_desperate_cities = []
    # desperate_cities = desperate()
    
    # while len(desperate_cities) > 5:
    #     desperate_cities.popitem()
    
    # for city, deficit in desperate_cities.items():
    #     final_desperate_cities.append((city,deficit))
        
    # # number_of_companies = Company.objects.all().count()
    # # number_of_depots = Subsidiaries.objects.filter(is_depot=True).count()
    # # number_of_s_stations = Subsidiaries.objects.filter(is_depot=False).count()
    # last_year_rev = get_aggregate_monthly_sales((datetime.now().year - 1))
    # # offers = Offer.objects.all().count()
    # # bulk_requests = FuelRequest.objects.filter(delivery_method="SELF COLLECTION").count()
    # # normal_requests = FuelRequest.objects.filter(delivery_method="DELIVERY").count()  # Change these 2 items
    # staff = ''
    # # new_orders = FuelRequest.objects.filter(date__gt=yesterday).count()
    # # clients = []
    # # stock = get_aggregate_stock()
    # # diesel = stock['diesel']
    # # petrol = stock['petrol']

    # trans = Transaction.objects.filter(is_complete=True).annotate(
    #     number_of_trans=Count('buyer')).order_by('-number_of_trans')[:10]
    # buyers = [client.buyer for client in trans]

    # branches = Subsidiaries.objects.filter(is_depot=True)

    # subs = []

    # for sub in branches:
    #     tran_amount = 0
    #     sub_trans = Transaction.objects.filter(supplier__subsidiary_id=sub.id,
    #                                            is_complete=True)
    #     for sub_tran in sub_trans:
    #         tran_amount += (sub_tran.offer.request.amount * sub_tran.offer.price)
    #     sub.tran_count = sub_trans.count()
    #     sub.tran_value = tran_amount
    #     subs.append(sub)

    # # sort subsidiaries by transaction value
    # sorted_subs = sorted(subs, key=lambda x: x.tran_value, reverse=True)

    # new_buyers = []
    # for buyer in buyers:
    #     total_transactions = buyers.count(buyer)
    #     buyers.remove(buyer)
    #     new_buyer_transactions = Transaction.objects.filter(is_complete=True).all()
    #     total_value = 0
    #     purchases = []
    #     number_of_trans = 0
    #     for tran in new_buyer_transactions:
    #         total_value += (tran.offer.request.amount * tran.offer.price)
    #         purchases.append(tran)
    #         number_of_trans += 1
    #     buyer.total_revenue = total_value
    #     buyer.purchases = purchases
    #     buyer.number_of_trans = total_transactions
    #     if buyer not in new_buyers:
    #         new_buyers.append(buyer)

    # clients = sorted(new_buyers, key=lambda x: x.total_revenue, reverse=True)

    # for company in companies:
    #     company.total_value = value[counter]
    #     company.num_transactions = num_trans[counter]
    #     counter += 1

    # clients = [company for company in  companies]

    # revenue = round(float(sum(value)))
    # revenue = get_aggregate_total_revenue()
    # revenue = '${:,.2f}'.format(revenue)
    # revenue = str(revenue) + '.00'

    # try:
    #     trans = Transaction.objects.filter(supplier=request.user, complete=true).count()/Transaction.objects.all().count()/100
    # except:
    #     trans = 0    
    # trans_complete = get_aggregate_transactions_complete_percentage()
    # inactive_depots = Subsidiaries.objects.filter(is_active=False, is_depot=True).count()
    # inactive_stations = Subsidiaries.objects.filter(is_active=False, is_depot=False).count()
    # approval_percentage = get_approved_company_complete_percentage()

    return render(request, 'noicDepot/statistics.html', {})
    