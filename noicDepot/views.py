from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect

from fuelUpdates.models import SordCompanyAuditTrail
from national.models import SordNationalAuditTrail, DepotFuelUpdate, NoicDepot
from noicDepot.util import sord_generator
from notification.models import Notification
from supplier.models import FuelAllocation
from users.models import Activity
from .forms import CollectionsForm
from .lib import *
from .models import Collections
from .decorators import user_role

today = date.today()
user = get_user_model()


@login_required
@user_role
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


@login_required()
@user_role
def dashboard(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    orders = SordNationalAuditTrail.objects.filter(assigned_depot=depot).all()
    return render(request, 'noicDepot/dashboard.html', {'orders': orders})


@login_required()
@user_role
def activity(request):
    activities = Activity.objects.filter(user=request.user).all()
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    return render(request, 'noicDepot/activity.html', {'activities': activities, 'depot': depot})


@login_required()
@user_role
def accepted_orders(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    orders_notifications = Notification.objects.filter(depot_id=depot.id).filter(action="ORDER").filter(is_read=False).all()
    for order in orders_notifications:
        if order is not None:
            order.is_read = True
            order.save()
        else:
            pass
     
    orders = Order.objects.filter(noic_depot=depot).all()
    return render(request, 'noicDepot/accepted_orders.html', {'orders': orders})


@login_required()
@user_role
def orders(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    orders_notifications = Notification.objects.filter(depot_id=depot.id).filter(action="ORDER").filter(is_read=False).all()
    num_of_new_orders = Notification.objects.filter(depot_id=depot.id).filter(action="ORDER").filter(is_read=False).count()
    orders = Order.objects.filter(noic_depot=depot).filter(allocated_fuel=False).all()
    # print(orders)
    for order in orders:
        if order is not None:
            alloc = SordNationalAuditTrail.objects.filter(order=order).first()
            if alloc is not None:
                order.allocation = alloc
    return render(request, 'noicDepot/orders.html', {'orders': orders, 'orders_notifications': orders_notifications, 'num_of_new_orders': num_of_new_orders,'allocate' : 'hide', 'release' : 'hide'})


@login_required()
@user_role
def stock(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    depot_stock = DepotFuelUpdate.objects.filter(depot=depot).all()

    orders = Order.objects.filter(noic_depot=depot).filter(allocated_fuel=False).all()
    noic_usd_diesel = 0
    noic_rtgs_diesel = 0
    noic_usd_petrol = 0
    noic_rtgs_petrol = 0

    for order in orders:
        if order.fuel_type.lower() == 'petrol':
            if order.currency == 'USD':
                noic_usd_petrol += order.quantity
            else:
                noic_rtgs_petrol += order.quantity

        else:
            if order.currency == 'USD':
                noic_usd_diesel += order.quantity
            else:
                noic_rtgs_diesel += order.quantity

    
    return render(request, 'noicDepot/stock.html', {'depot_stock': depot_stock, 'depot': depot, 'noic_usd_diesel':noic_usd_diesel, 'noic_rtgs_diesel': noic_rtgs_diesel, 'noic_usd_petrol': noic_usd_petrol, 'noic_rtgs_petrol': noic_rtgs_petrol})


@login_required()
@user_role
def upload_release_note(request, id):
    allocation = SordNationalAuditTrail.objects.filter(id=id).first()
    if request.method == 'POST':
        allocation.release_date = request.POST['release_date']
        allocation.release_note = True
        allocation.save()

        action = "Uploading Release Note"
        description = f"You have uploaded release note to {allocation.company.name}"
        Activity.objects.create(company=allocation.company, user=request.user, action=action, description=description, reference_id=allocation.id)
        messages.success(request, "Release note successfully created")
        return redirect('noicDepot:dashboard')


@login_required()
@user_role
def payment_approval(request, id):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    noic_capacity = DepotFuelUpdate.objects.filter(depot=depot).first()
    
    orders = Order.objects.filter(noic_depot=depot).all()
    for order in orders:
        if order is not None:
            alloc = SordNationalAuditTrail.objects.filter(order=order).first()
            if alloc is not None:
                order.allocation = alloc
    order = Order.objects.filter(id=id).first()
    if order.fuel_type.lower() == "petrol":
        if order.currency.lower() == 'usd':
            if noic_capacity.usd_petrol == 0.00:
                messages.warning(request, "You Have Insufficient Petrol To Approve This Order")
                return redirect(f'noicDepot:orders')
        else:
            if noic_capacity.rtgs_petrol == 0.00:
                messages.warning(request, "You Have Insufficient Petrol To Approve This Order")
                return redirect(f'noicDepot:orders')
    if order.fuel_type.lower() == "diesel":
        if order.currency.lower() == 'usd':
            if noic_capacity.usd_diesel == 0.00:
                print('_______________________________dsdnd____________')
                messages.warning(request, "You Have Insufficient Diesel To Approve This Order")

                return redirect(f'noicDepot:orders')
        else:
            if noic_capacity.rtgs_diesel == 0.00:
                messages.warning(request, "You Have Insufficient Diesel To Approve This Order")

                return redirect(f'noicDepot:orders')            

    order.payment_approved = True
    order.save()

    action = "Approving Payment"
    description = f"You have approved order payment from {order.company.name}"
    Activity.objects.create(company=order.company, user=request.user,
                                    action=action, description=description, reference_id=order.id)
    messages.success(request, 'payment approved successfully')
    return render(request, 'noicDepot/orders.html', {'orders': orders, 'order': order, 'allocate' : 'show'})


@login_required()
@user_role
def view_release_note(request, id):
    allocation = SordNationalAuditTrail.objects.filter(id=id).first()
    allocation.admin = User.objects.filter(company=allocation.company).filter(user_type='S_ADMIN').first()
    allocation.rep = request.user
    context = {
        'allocation': allocation
    }
    return render(request, 'noicDepot/release_note.html', context=context)


@login_required()
@user_role
def download_release_note(request, id):
    allocation = SordNationalAuditTrail.objects.filter(id=id).first()
    allocation.admin = User.objects.filter(company=allocation.company).filter(user_type='S_ADMIN').first()
    allocation.rep = request.user
    context = {
        'allocation': allocation
    }
    return render(request, 'noicDepot/r_note.html', context=context)


@login_required()
@user_role
def allocate_fuel(request, id):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    orders = Order.objects.filter(noic_depot=depot).all()
    for order in orders:
        if order is not None:
            alloc = SordNationalAuditTrail.objects.filter(order=order).first()
            if alloc is not None:
                order.allocation = alloc
    order = Order.objects.filter(id=id).first()
   
    if request.method == 'POST':
        if request.POST['fuel_type'].lower() == 'petrol':
            if request.POST['currency'] == 'USD':
                depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
                noic_capacity = DepotFuelUpdate.objects.filter(depot=depot).first()
                if float(request.POST['quantity']) > noic_capacity.usd_petrol:
                    # messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.usd_petrol}L')
                    balance = float(request.POST['quantity']) - noic_capacity.usd_petrol
                    sord_object = SordNationalAuditTrail.objects.create(price=noic_capacity.usd_petrol_price, order=order, assigned_depot=depot, company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=(float(request.POST['quantity'])-float(balance)))
                    sord_object.sord_no = sord_generator('p', sord_object.id)
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity']) - balance
                    company_update.petrol_price = noic_capacity.usd_petrol_price
                    company_update.save()
                    order.quantity -= noic_capacity.usd_petrol
                    noic_capacity.usd_petrol = 0
                    order.allocated_fuel = True
                    order.save()
                    noic_capacity.save()

                    action = "Fuel Allocation"
                    description = f"You have allocated USD petrol to {order.company.name}"
                    Activity.objects.create(company=order.company, user=request.user, action=action, description=description, reference_id=order.id)
                    messages.success(request, f'fuel allocated successfully, with {balance} remaining')
                    return render(request, 'noicDepot/orders.html', {'orders': orders, 'sord_object': sord_object, 'release' : 'show'})
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

                    action = "Fuel Allocation"
                    description = f"You have allocated USD petrol to {order.company.name}"
                    Activity.objects.create(company=order.company, user=request.user, action=action, description=description, reference_id=order.id)
                    messages.success(request, 'fuel allocated successfully')
                    return render(request, 'noicDepot/orders.html', {'orders': orders, 'sord_object': sord_object, 'release' : 'show'})
            
            else:
                depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
                noic_capacity = DepotFuelUpdate.objects.filter(depot=depot).first()
                if float(request.POST['quantity']) > noic_capacity.rtgs_petrol:
                    # messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.rtgs_petrol}L')
                    balance = float(request.POST['quantity']) - noic_capacity.rtgs_petrol
                    sord_object = SordNationalAuditTrail.objects.create(price=noic_capacity.rtgs_petrol_price, order=order, assigned_depot=depot, company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=(float(request.POST['quantity'])-float(balance)))
                    sord_object.sord_no = sord_generator('p', sord_object.id)
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity']) - balance
                    company_update.petrol_price = noic_capacity.rtgs_petrol_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.quantity -= noic_capacity.rtgs_petrol
                    noic_capacity.rtgs_petrol = 0
                    order.save()
                    noic_capacity.save()

                    action = "Fuel Allocation"
                    description = f"You have allocated RTGS petrol to {order.company.name}"
                    Activity.objects.create(company=order.company, user=request.user, action=action, description=description, reference_id=order.id)
                    messages.success(request, f'fuel allocated successfully, with {balance} remaining')
                    return render(request, 'noicDepot/orders.html', {'orders': orders, 'sord_object': sord_object, 'release' : 'show'})
                else:
                    noic_capacity.rtgs_petrol -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(price=noic_capacity.rtgs_petrol_price, order=order, assigned_depot=depot, company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_generator('p', sord_object.id)
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.petrol_price = noic_capacity.rtgs_petrol_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()

                    action = "Fuel Allocation"
                    description = f"You have allocated RTGS petrol to {order.company.name}"
                    Activity.objects.create(company=order.company, user=request.user, action=action, description=description, reference_id=order.id)
                    messages.success(request, 'fuel allocated successfully')
                    return render(request, 'noicDepot/orders.html', {'orders': orders, 'sord_object': sord_object, 'release' : 'show'})
            

        else:
            if request.POST['currency'] == 'USD':
                depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
                noic_capacity = DepotFuelUpdate.objects.filter(depot=depot).first()
                if float(request.POST['quantity']) > noic_capacity.usd_diesel:
                    # messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.usd_diesel}L')
                    balance = float(request.POST['quantity']) - noic_capacity.usd_diesel
                    sord_object = SordNationalAuditTrail.objects.create(price=noic_capacity.usd_diesel_price, order=order, assigned_depot=depot, company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity'])-float(balance))
                    sord_object.sord_no = sord_generator('d', sord_object.id)
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_diesel += float(request.POST['quantity']) - balance
                    company_update.diesel_price = noic_capacity.usd_diesel_price
                    company_update.save()
                    order.quantity = noic_capacity.usd_diesel
                    order.allocated_fuel = True
                    noic_capacity.usd_diesel = 0
                    order.save()
                    noic_capacity.save()

                    action = "Fuel Allocation"
                    description = f"You have allocated USD diesel to {order.company.name}"
                    Activity.objects.create(company=order.company, user=request.user, action=action, description=description, reference_id=order.id)
                    messages.success(request, f'fuel allocated successfully, with {balance} remaining')
                    return render(request, 'noicDepot/orders.html', {'orders': orders, 'sord_object': sord_object, 'release' : 'show'})
                else:
                    noic_capacity.usd_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(price=noic_capacity.usd_diesel_price, order=order, assigned_depot=depot, company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_generator('d', sord_object.id)
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_diesel += float(request.POST['quantity'])
                    company_update.usd_diesel_price = noic_capacity.usd_diesel_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()

                    action = "Fuel Allocation"
                    description = f"You have allocated USD diesel to {order.company.name}"
                    Activity.objects.create(company=order.company, user=request.user, action=action, description=description, reference_id=order.id)
                    messages.success(request, 'fuel allocated successfully')
                    return render(request, 'noicDepot/orders.html', {'orders': orders, 'sord_object': sord_object, 'release' : 'show'})
            
            
            else:
                depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
                noic_capacity = DepotFuelUpdate.objects.filter(depot=depot).first()
                if float(request.POST['quantity']) > noic_capacity.rtgs_diesel:
                    # messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.rtgs_diesel}L')
                    balance = float(request.POST['quantity']) - noic_capacity.rtgs_diesel
                    sord_object = SordNationalAuditTrail.objects.create(price=noic_capacity.rtgs_diesel_price, order=order, assigned_depot=depot, company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity'])-float(balance))
                    fuel_type = request.POST['fuel_type']
                    sord_object.sord_no = sord_generator(fuel_type[0], sord_object.id)
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_diesel += float(request.POST['quantity']) - balance
                    company_update.rtgs_diesel_price = noic_capacity.rtgs_diesel_price
                    company_update.save()
                    order.quantity -= noic_capacity.noic_capacity.rtgs_diesel
                    order.allocated_fuel = True
                    noic_capacity.rtgs_diesel = 0
                    noic_capacity.save()
                    order.save()

                    action = "Fuel Allocation"
                    description = f"You have allocated RTGS diesel to {order.company.name}"
                    Activity.objects.create(company=order.company, user=request.user, action=action, description=description, reference_id=order.id)
                    messages.success(request, f'fuel allocated successfully, with {balance} remaining')
                    return render(request, 'noicDepot/orders.html', {'orders': orders, 'sord_object': sord_object, 'release' : 'show'})
                else:
                    noic_capacity.rtgs_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(price=noic_capacity.rtgs_diesel_price, order=order, assigned_depot=depot, company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    fuel_type = request.POST['fuel_type']
                    sord_object.sord_no = sord_generator(fuel_type[0], sord_object.id)
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_diesel += float(request.POST['quantity'])
                    company_update.diesel_price = noic_capacity.rtgs_diesel_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()

                    action = "Fuel Allocation"
                    description = f"You have allocated RTGS diesel to {order.company.name}"
                    Activity.objects.create(company=order.company, user=request.user, action=action, description=description, reference_id=order.id)
                    messages.success(request, 'fuel allocated successfully')
                    return render(request, 'noicDepot/orders.html', {'orders': orders, 'sord_object': sord_object, 'release' : 'show'})


@login_required()
@user_role
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


@login_required()
@user_role
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


@login_required()
@user_role
def profile(request):
    user = request.user
    return render(request, 'noicDepot/profile.html', {'user': user})


@login_required()
@user_role
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
            stock.depot = depot

            print(f'______________________{stock}_________________')
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


@login_required()
@user_role
def statistics(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    weekly_rev = get_weekly_sales(True,depot)
    monthly_rev = get_aggregate_monthly_sales(datetime.now().year, depot)
    last_year_rev = get_aggregate_monthly_sales((datetime.now().year - 1), depot)
    last_week_rev = get_weekly_sales(False,depot)
    order_completions = str(round((Order.objects.filter(payment_approved=True, noic_depot=depot).count()/Order.objects.filter(noic_depot=depot).count() * 100))) + " %"
    allocations = SordNationalAuditTrail.objects.filter(assigned_depot=depot).count()
    stock = DepotFuelUpdate.objects.filter(depot=depot).first()
    revenue = 0
    for order in Order.objects.filter(payment_approved=True):
        revenue += order.amount_paid

    return render(request, 'noicDepot/statistics.html', {'weekly_rev': weekly_rev, 'last_week_rev':last_week_rev, 'monthly_rev':monthly_rev,
                    'depot':depot, 'order_completions':order_completions, 'allocations':allocations, 'stock':stock,'revenue': revenue })


@login_required()
@user_role
def collections(request):
    context = {
        'collections': Collections.objects.filter(),
        'form': CollectionsForm()
    }
    if request.method == 'POST':
        collection = Collections.objects.filter(id=request.POST.get('collection_id')).first()
        collection.transporter = request.POST.get('transporter')
        collection.truck_reg = request.POST.get('truck_reg')
        collection.trailer_reg = request.POST.get('trailer_reg')
        collection.driver = request.POST.get('driver')
        collection.driver_id = request.POST.get('driver_id')
        collection.date_collected = date.today()
        collection.time_collected = datetime.today().time()
        collection.has_collected = True
        collection.save()

        messages.success(request, 'Collection saved successfully')
        return redirect('noicDepot:collections')

    return render(request, 'noicDepot/collections.html', context=context)


@login_required()
@user_role
def hg_notifier(request, id):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    if id == 1:
        message = 'Requesting for more USD diesel fuel'
        Notification.objects.create(message=message, reference_id=id, responsible_depot=depot, action="MORE_FUEL")
    elif id == 2:
        message = 'Requesting for more RTGS diesel fuel'
        Notification.objects.create(message=message, reference_id=id, responsible_depot=depot, action="MORE_FUEL")
    elif id ==3:
        message = 'Requesting for more USD petrol fuel'
        Notification.objects.create(message=message, reference_id=id, responsible_depot=depot, action="MORE_FUEL")
    else:
        message = 'Requesting for more RTGS petrol fuel'
        Notification.objects.create(message=message, reference_id=id, responsible_depot=depot, action="MORE_FUEL")
    messages.success(request, "Request for more fuel made successfully")
    return redirect('noicDepot:stock')