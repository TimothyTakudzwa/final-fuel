from itertools import chain
from operator import attrgetter

from django.contrib.auth import authenticate, update_session_auth_hash, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.contrib import messages
from django.db.models import Q

import secrets

from buyer.utils import render_to_pdf
from company.models import Company
from users.models import Audit_Trail
from datetime import date, time, datetime
from buyer.constants2 import industries, job_titles
from buyer.forms import BuyerUpdateForm
from buyer.models import FuelRequest
from accounts.models import Account
from users.models import AuditTrail
from .forms import PasswordChange, RegistrationForm, \
    RegistrationEmailForm, UserUpdateForm, FuelRequestForm, CreateCompany, OfferForm
from .models import Transaction, FuelAllocation, TokenAuthentication, SordSubsidiaryAuditTrail, Offer, Subsidiaries, SuballocationFuelUpdate, SubsidiaryFuelUpdate ,DeliverySchedule
from notification.models import Notification
from django.contrib.auth import get_user_model
from whatsapp.helper_functions import send_message
from .lib import *

User = get_user_model()

# today's date
today = date.today()

@login_required
def edit_delivery_schedule(request):
    if request.method == "POST":
        delivery_schedule = DeliverySchedule.objects.filter(id=int(request.POST['delivery_id'])).first()
        delivery_schedule.driver_name = request.POST['driver_name']
        delivery_schedule.phone_number = request.POST['phone_number']
        delivery_schedule.id_number = request.POST['id_number']
        delivery_schedule.vehicle_reg = request.POST['vehicle_reg']
        delivery_schedule.delivery_time = request.POST['delivery_time']
        delivery_schedule.transport_company = request.POST['transport_company']       
        delivery_schedule.save()
        messages.success(request, "Schedule Successfully Updated")
        return redirect('supplier:delivery_schedules')

@login_required
def clients(request):
    clients = Account.objects.filter(supplier_company=request.user.company)
    return render(request, 'supplier/clients.html', {'clients': clients})


@login_required
def verify_client(request,id):
    client = get_object_or_404(Account, id=id)
    if not client.is_verified:
        client.is_verified = True
        client.save()
        messages.success(request, f'{client.buyer_company.name} Successfully Verified')
        return redirect('supplier:clients')
    client.is_verified = False
    client.save()
    messages.success(request, f'{client.buyer_company.name}"s Verification Overturned')
    return redirect('supplier:clients')

@login_required
def view_client_id_document(request,id):
    client = Account.objects.filter(id=id).first()
    if client:
        filename = client.id_document.name.split('/')[-1]
        response = HttpResponse(client.id_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document Not Found')
        redirect('supplier:clients')
    return response


@login_required
def view_application_id_document(request,id):
    client = Account.objects.filter(id=id).first()
    if client:
        filename = client.application_document.name.split('/')[-1]
        response = HttpResponse(client.application_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document Not Found')
        redirect('supplier:clients')
    return response


@login_required
def client_transaction_history(request,id):
    client = Account.objects.filter(id=id).first()

    contribution = get_customer_contributions(request.user.id, client.buyer_company)
    cash_contribution = get_customer_contributions(request.user.id, client.buyer_company)[1]
    total_cash = client_revenue(request.user.id, client.buyer_company)
    all_requests, todays_requests = total_requests(client.buyer_company)


    trns = Transaction.objects.filter(supplier=request.user,buyer__company=client.buyer_company)
    transactions = []
    for tran in trns:
        tran.revenue = tran.offer.request.amount * tran.offer.price
        transactions.append(tran)

    return render(request, 'supplier/client_activity.html', {'transactions': transactions, 'client': client,
    'contribution':contribution, 'cash_contribution':cash_contribution, 'total_cash':total_cash,
     'all_requests':all_requests, 'todays_requests': todays_requests })



        
@login_required
def delivery_schedules(request):
    if request.method == 'POST':
        supplier_document = request.FILES.get('supplier_document')
        delivery_id = request.POST.get('delivery_id')
        schedule = DeliverySchedule.objects.get(id=delivery_id)
        schedule.supplier_document = supplier_document
        schedule.save()
        messages.success(request, "File Successfully Uploaded")
        msg = f"Delivery Confirmed for {schedule.transaction.buyer.company}, Click To View Confirmation Document"
        Notification.objects.create(user=request.user,action='DELIVERY', message=msg, reference_id=schedule.id)
        return redirect('delivery_schedules')
        
    schedules = DeliverySchedule.objects.filter(transaction__supplier=request.user).all()
    for schedule in schedules:
        if schedule.transaction.offer.delivery_method.lower() == 'delivery':
            schedule.delivery_address = schedule.transaction.offer.request.delivery_address
        else:
            schedule.delivery_address = schedule.transaction.offer.collection_address
    return render(request, 'supplier/delivery_schedules.html', {'schedules': schedules})    


@login_required()
def change_password(request):
    context = {
        'title': 'Fuel Finder | Change Password',
        'password_change': PasswordChange(user=request.user)
    }
    if request.method == 'POST':
        old = request.POST.get('old_password')
        new1 = request.POST.get('new_password1')
        new2 = request.POST.get('new_password2')

        if authenticate(request, username=request.user.username, password=old):
            if new1 != new2:
                messages.warning(request, "Passwords Don't Match")
                return redirect('change-password')
            elif new1 == old:
                messages.warning(request, "New password can not be similar to the old one")
                return redirect('change-password')
            elif len(new1) < 8:
                messages.warning(request, "Password is too short")
                return redirect('change-password')
            elif new1.isnumeric():
                messages.warning(request, "Password can not be entirely numeric!")
            elif not new1.isalnum():
                messages.warning(request, "Password should be alphanumeric")
                return redirect('change-password')
            else:
                user = request.user
                user.set_password(new1)
                user.save()
                update_session_auth_hash(request, user)

                messages.success(request, 'Password Successfully Changed')
                return redirect('account')
        else:
            messages.warning(request, 'Wrong Old Password, Please Try Again')
            return redirect('change-password')
    return render(request, 'supplier/change_password.html', context=context)


@login_required()
def account(request):
    sub = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
    # if subsidiary is not None:
    #     subsidiary_name = subsidiary.name
    # else:
    #     subsidiary_name = "Not Set"
    return render(request, 'supplier/user_profile.html', {'sub':sub})


@login_required()
def fuel_request(request):
    sub = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
    if sub:
        if sub.praz_reg_num != None:
            requests = FuelRequest.objects.filter(is_deleted=False ,wait=True, is_complete=False).all()
            direct_requests =  FuelRequest.objects.filter(is_deleted=False, is_complete=False, is_direct_deal=True, last_deal=request.user.subsidiary_id).all()
            requests = list(chain(requests, direct_requests))
            requests.sort(key = attrgetter('date', 'time'), reverse = True)
        else:
            requests = FuelRequest.objects.filter(~Q(name__company__is_govnt_org=True)).filter(is_deleted=False ,wait=True, is_complete=False).all()
            direct_requests =  FuelRequest.objects.filter(~Q(name__company__is_govnt_org=True)).filter(is_deleted=False, is_complete=False, is_direct_deal=True, last_deal=request.user.subsidiary_id).all()
            requests = list(chain(requests, direct_requests))
            requests.sort(key = attrgetter('date', 'time'), reverse = True)

        for buyer_request in requests:
            if buyer_request.payment_method == 'USD':
                fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(payment_type='USD').first()
            elif buyer_request.payment_method == 'RTGS':
                fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(payment_type='RTGS').first()
            elif buyer_request.payment_method == 'USD & RTGS':
                fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(payment_type='USD & RTGS').first()
            else:
                fuel = None
            if buyer_request.dipping_stick_required==buyer_request.meter_required==buyer_request.pump_required==False:
                buyer_request.no_equipments = True
            if buyer_request.cash==buyer_request.ecocash==buyer_request.swipe==buyer_request.usd==False:
                buyer_request.no_payment = True
            if not buyer_request.delivery_address.strip():
                buyer_request.delivery_address = f'N/A'
            if Offer.objects.filter(supplier_id=request.user, request_id=buyer_request).exists():
                offer = Offer.objects.filter(supplier_id=request.user, request_id=buyer_request).first()
                buyer_request.my_offer = f'{offer.quantity}ltrs @ ${offer.price}'
                buyer_request.offer_price = offer.price
                buyer_request.offer_quantity = offer.quantity
                buyer_request.offer_id = offer.id
            else:
                buyer_request.my_offer = 'No Offer'
                buyer_request.offer_id = 0
            if fuel:
                if buyer_request.fuel_type.lower() == 'petrol':

                    buyer_request.price = fuel.petrol_price
                else:
                    buyer_request.price = fuel.diesel_price
            else:
                buyer_request.price = 0.00
    requests = None        
    return render(request, 'supplier/fuel_request.html', {'requests':requests})

def new_fuel_request(request, id):
    requests = FuelRequest.objects.filter(id = id,wait=True).all()
    return render(request, 'supplier/new_fuel_request.html', {'requests':requests})

def accepted_offer(request, id):
    transactions = Transaction.objects.filter(id=id).all()
    return render(request, 'supplier/new_transaction.html', {'transactions':transactions})

def rejected_offer(request, id):
    offers = Offer.objects.filter(id=id).all()
    return render(request, 'supplier/my_offer.html', {'offers':offers})



@login_required
def available_stock(request):
    updates = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).all()

    return render(request, 'supplier/available_fuel.html', {'updates': updates})

@login_required()
def stock_update(request,id):
    updates = SuballocationFuelUpdate.objects.filter(id=id).first()
    available_petrol = updates.petrol_quantity
    available_diesel = updates.diesel_quantity
    suballocations = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).all()
    subsidiary_fuel = SubsidiaryFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).first()
    if request.method == 'POST':
        if SuballocationFuelUpdate.objects.filter(id=id).exists():
            fuel_update = SuballocationFuelUpdate.objects.filter(id=id).first()
            if request.POST['fuel_type'] == 'Petrol':
                if float(request.POST['quantity']) > available_petrol:
                    messages.warning(request, 'You can only reduce your petrol quantity')
                    return redirect('available_stock')
                fuel_reduction = fuel_update.petrol_quantity - float(request.POST['quantity'])
                fuel_update.petrol_quantity = float(request.POST['quantity'])
                subsidiary_fuel.petrol_quantity = subsidiary_fuel.petrol_quantity - fuel_reduction
                subsidiary_fuel.save()

                sord_update(request, request.user, fuel_reduction, 'Fuel Update', 'Petrol', fuel_update.payment_type)

            else:
                if float(request.POST['quantity']) > available_diesel:
                    messages.warning(request, 'You can only reduce your diesel quantity')
                    return redirect('available_stock')
                fuel_reduction = fuel_update.diesel_quantity - float(request.POST['quantity'])
                fuel_update.diesel_quantity = float(request.POST['quantity'])
                subsidiary_fuel.diesel_quantity = subsidiary_fuel.diesel_quantity - fuel_reduction
                subsidiary_fuel.save()

                sord_update(request, request.user, fuel_reduction, 'Fuel Update', 'Diesel', fuel_update.payment_type)

            fuel_update.cash = request.POST['cash']
            fuel_update.swipe = request.POST['swipe']
            if fuel_update.payment_type != 'USD':
                fuel_update.ecocash = request.POST['ecocash']
            fuel_update.save()
            messages.success(request, 'Fuel successfully updated')
    return redirect('available_stock')


def offer(request, id):
    form = OfferForm(request.POST)
    if request.method == "POST":
        if float(request.POST.get('price')) != 0 and float(request.POST.get('quantity')) != 0:
            fuel_request = FuelRequest.objects.get(id=id)
            fuel_reserve = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id, payment_type = 'USD & RTGS').first()
            if fuel_request.payment_method == 'USD':
                fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id, payment_type = 'USD').first()
            elif fuel_request.payment_method == 'RTGS':
                 fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id, payment_type = 'RTGS').first()
            subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
            
            if fuel_request.fuel_type.lower() == 'petrol':
                if fuel_reserve is not None:
                    available_fuel = fuel.petrol_quantity + fuel_reserve.petrol_quantity
                else:
                    available_fuel = fuel.petrol_quantity
            elif fuel_request.fuel_type.lower() == 'diesel':
                if fuel_reserve is not None:
                    available_fuel = fuel.diesel_quantity + fuel_reserve.diesel_quantity
                else:
                    available_fuel = fuel.diesel_quantity
            offer_quantity = int(request.POST.get('quantity'))
            quantity = fuel_request.amount

            if offer_quantity <= available_fuel:
                if offer_quantity <= quantity:
                    offer = Offer()
                    offer.supplier = request.user
                    offer.request = fuel_request
                    offer.price = request.POST.get('price')    
                    offer.quantity = request.POST.get('quantity')
                    offer.fuel_type = request.POST.get('fuel_type')
                    offer.usd = True if request.POST.get('usd') == "on" else False
                    offer.cash = True if request.POST.get('cash') == "on" else False
                    offer.ecocash = True if request.POST.get('ecocash') == "on" else False
                    offer.swipe = True if request.POST.get('swipe') == "on" else False
                    delivery_method = request.POST.get('delivery_method')
                    if not delivery_method.strip():
                        offer.delivery_method = 'Delivery'
                    else:
                        offer.delivery_method = delivery_method
                    collection_address = request.POST.get('street_number') + " " + request.POST.get('street_name') + " " + request.POST.get('location')
                    if not collection_address.strip() and delivery_method.lower() == 'self collection':
                        offer.collection_address = subsidiary.location
                    else:
                        offer.collection_address = collection_address
                    offer.pump_available = True if request.POST.get('pump_available') == "on" else False
                    offer.dipping_stick_available = True if request.POST.get('dipping_stick_available') == "on" else False
                    offer.meter_available = True if request.POST.get('meter_available') == "on" else False
                    offer.save()
                    
                    messages.success(request, 'Offer uploaded successfully')


                    message = f'You have a new offer of {offer_quantity}L {fuel_request.fuel_type.lower()} at ${offer.price} from {request.user.company.name.title()}  for your request of {fuel_request.amount}L'
                    Notification.objects.create(message = message, user = fuel_request.name, reference_id = offer.id, action = "new_offer")
                    click_url = f'https://fuelfinderzim.com/new_fuel_offer/{offer.id}'
                    if offer.request.name.activated_for_whatsapp:
                        send_message(offer.request.name.phone_number,f'Your have received a new offer of {offer_quantity}L {fuel_request.fuel_type.lower()} at ${offer.price} from {request.user.company.name} {request.user.last_name} for your request of {fuel_request.amount}L click {click_url} to view details')
                    action = f"{request.user}  made an offer of {offer_quantity}L @ {request.POST.get('price')} to a request made by {fuel_request.name.username}"
                    service_station = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
                    reference = 'offers'
                    reference_id = fuel_request.id
                    Audit_Trail.objects.create(company=request.user.company,service_station=service_station,user=request.user,action=action,reference=reference,reference_id=reference_id)
                    return redirect('fuel-request')
                else:
                    messages.warning(request, 'You can not make an offer greater than the requested fuel quantity!')
                    return redirect('fuel-request')
            else:
                messages.warning(request, 'You can not offer fuel more than the available fuel stock')
                return redirect('fuel-request')
        else:
            messages.warning(request, "Please provide a price to complete an offer")
            return redirect('fuel-request')
    return render(request, 'supplier/fuel_request.html')

@login_required
def edit_offer(request, id):
    offer = Offer.objects.get(id=id)
    fuel_reserve =SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id, payment_type = 'USD & RTGS').first()
    if request.method == 'POST':
        if offer.request.payment_method == 'USD':
            fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id, payment_type = 'USD').first()
        elif offer.request.payment_method == 'RTGS':
            fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id, payment_type = 'RTGS').first()
        subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
        
        if offer.request.fuel_type.lower() == 'petrol':
            if fuel_reserve is not None:
                available_fuel = fuel.petrol_quantity + fuel_reserve.petrol_quantity
            else:
                available_fuel = fuel.petrol_quantity
        elif fuel_request.fuel_type.lower() == 'diesel':
            if fuel_reserve is not None:
                available_fuel = fuel.diesel_quantity + fuel_reserve.diesel_quantity
            else:
                available_fuel = fuel.diesel_quantity
        new_offer = int(request.POST.get('quantity'))
        request_quantity = offer.request.amount
        if new_offer <= available_fuel:
            if new_offer <= request_quantity:
                offer.price = request.POST.get('price')      
                offer.quantity = request.POST.get('quantity')
                offer.usd = True if request.POST.get('usd') == "on" else False
                offer.cash = True if request.POST.get('cash') == "on" else False
                offer.ecocash = True if request.POST.get('ecocash') == "on" else False
                offer.swipe = True if request.POST.get('swipe') == "on" else False
                delivery_method = request.POST.get('delivery_method1')
                if not delivery_method.strip():
                    offer.delivery_method = 'Delivery'
                else:
                    offer.delivery_method = delivery_method
                collection_address = request.POST.get('street_number') + " " + request.POST.get('street_name') + " " + request.POST.get('location')
                if not collection_address.strip() and delivery_method.lower() == 'self collection':
                    offer.collection_address = subsidiary.location
                else:
                    offer.collection_address = collection_address
                offer.pump_available = True if request.POST.get('pump_available') == "on" else False
                offer.dipping_stick_available = True if request.POST.get('dipping_stick_available') == "on" else False
                offer.meter_available = True if request.POST.get('meter_available') == "on" else False
                offer.save()
                messages.success(request, 'Offer successfully updated')
                message = f'You have an updated offer of {new_offer}L {offer.request.fuel_type.lower()} at ${offer.price} from {request.user.company.name.title()} for your request of {offer.request.amount}L'
                Notification.objects.create(message = message, user = offer.request.name, reference_id = offer.id, action = "new_offer")
                return redirect('my_offers')
            else:
                messages.warning(request, 'You can not make an offer greater than the requested fuel quantity!')
                return redirect('my_offers')
        else:
            messages.warning(request, 'You can not offer fuel more than the available fuel stock')
            return redirect('my_offers')
    return render(request, 'supplier/fuel_request.html', {'offer': offer})


@login_required
def transaction(request):
    today = datetime.now().strftime("%m/%d/%y")
    transporters = Company.objects.filter(company_type="TRANSPORTER").all()
    transactions = []
    for tran in Transaction.objects.filter(supplier=request.user).all():
        delivery_sched = DeliverySchedule.objects.filter(transaction=tran).first()
        if delivery_sched:
            tran.delivery_sched = delivery_sched
        transactions.append(tran)    
    context= { 
       'transactions' : transactions,
       'transporters' : transporters,
       'today': today
        }
    return render(request, 'supplier/transactions.html',context=context)

@login_required
def create_delivery_schedule(request):
    if request.method == 'POST':
        schedule = DeliverySchedule.objects.create(
            date=request.POST['delivery_date'],
            transaction = Transaction.objects.filter(id=int(request.POST['transaction'])).first(),
            driver_name = request.POST['driver_name'],
            phone_number = request.POST['phone_number'],
            id_number = request.POST['id_num'],
            transport_company = request.POST['transport_company'],
            vehicle_reg = request.POST['vehicle_reg'],
            delivery_time = request.POST['delivery_time']
        )
        messages.success(request,"Schedule Successfully Created")
        message = f"{schedule.transaction.supplier.company} has created a delivery schedule for you, Click To View Schedule"
        Notification.objects.create(user=schedule.transaction.buyer,action='schedule', message=message, reference_id=schedule.id)
        
        return redirect('transaction')
        

def allocated_quantity(request):
    allocations = FuelAllocation.objects.filter(allocated_subsidiary_id= request.user.subsidiary_id).all()
    return render(request, 'supplier/allocated_quantity.html', {'allocations': allocations})


def activate_whatsapp(request):
    user = User.objects.filter(id=request.user.id).first()
    if user.activated_for_whatsapp == False:
        user.activated_for_whatsapp = True
        user.save()
        messages.success(request, 'Your WhatsApp has been activated successfully')
        return redirect('fuel-request')

    else:
        user.activated_for_whatsapp = False
        user.save()
        messages.warning(request, 'Your WhatsApp has been deactivated successfully')
        return redirect('fuel-request')


def verification(request, token, user_id):
    user = User.objects.get(id=user_id)
    token_check = TokenAuthentication.objects.filter(user=user, token=token)  
    if token_check.exists():
        token_not_used = TokenAuthentication.objects.filter(user=user, used=False)
        if token_not_used.exists():
            form = BuyerUpdateForm
            check = User.objects.filter(id=user_id)
            if check.exists():
                user = User.objects.get(id=user_id)
                if user.user_type == 'BUYER':
                    companies = Company.objects.filter(company_type='CORPORATE').all()
                else:
                    companies = Company.objects.filter(company_type='SUPPLIER').all()

            if request.method == 'POST':
                user = User.objects.get(id=user_id)
                form = BuyerUpdateForm(request.POST, request.FILES, instance=user)
                if form.is_valid():
                    form.save()
                    company_exists = Company.objects.filter(name=request.POST.get('company')).exists()
                    if company_exists:
                        selected_company =Company.objects.filter(name=request.POST.get('company')).first()
                        user.company = selected_company
                        user.is_active = True
                        user.stage = 'menu'
                        user.save()
                        TokenAuthentication.objects.filter(user=user).update(used=True)
                        if user.user_type == 'BUYER':
                            return redirect('login')
                        else:
                            user.is_active = False
                            user.is_waiting = True
                            user.stage = 'menu'
                            user.save()
                            my_admin = User.objects.filter(company=selected_company,user_type='S_ADMIN').first()
                            if my_admin is not None:
                                return render(request,'supplier/final_registration.html',{'my_admin': my_admin})
                            else:
                                return render(request,'supplier/final_reg.html')
                    else:
                        selected_company =Company.objects.create(name=request.POST.get('company'))
                        user.is_active = False
                        user.is_waiting = True
                        if user.user_type == 'SUPPLIER':
                            user.user_type = 'S_ADMIN'
                        # selected_company = Company.objects.create(name=request.POST.get('company'))
                        selected_company.save()
                        user.company = selected_company
                        user.is_waiting = True
                        user.save() 
                        TokenAuthentication.objects.filter(user=user).update(used=True)
                        return redirect('supplier:create_company', id=user.id)
                    
            else:
                return render(request, 'supplier/verify.html', {'form': form, 'industries': industries, 'companies': companies, 'jobs': job_titles})
        else:
            messages.warning(request, 'This link has been used before')
            return redirect('buyer-register')
        
    else:
        messages.warning(request, 'Wrong verification token, kindly follow the link send in the email')
        return redirect('login')
    
    return render(request, 'supplier/verify.html', {'form': form, 'industries': industries, 'companies': companies, 'jobs': job_titles})

def create_company(request, id):
    form = CreateCompany()
    user = User.objects.filter(id=id).first()
    user_type = user.user_type
    form.initial['company_name'] = user.company.name

    if request.method == 'POST':
        form = CreateCompany(request.POST)
        if form.is_valid():
            if user_type == 'BUYER':
                company_name = request.POST.get('company_name')
                address = request.POST.get('address')
                is_govnt_org = request.POST.get('is_govnt_org')
                logo = request.FILES.get('logo')
                company_name = user.company.name
                Company.objects.filter(name=company_name).update(name = company_name,address = address, logo = logo,is_govnt_org=is_govnt_org)
                return redirect('login')

            else:
                company_name = request.POST.get('company_name')
                address = request.POST.get('address')
                logo = request.FILES.get('logo')
                iban_number = request.POST.get('iban_number')
                license_number = request.POST.get('license_number')
                new_company = Company.objects.filter(name=company_name).update(name = company_name, address = address, logo = logo, iban_number = iban_number, license_number = license_number)
                new_company.save()
                CompanyFuelUpdate.objects.create(company=new_company)
                return render(request,'supplier/final_reg.html')
            
    return render(request, 'supplier/create_company.html', {'form': form, 'user_type':user_type })

    
def company(request):
    subsidiary = Subsidiaries.objects.filter(id = request.user.subsidiary_id).first()
    num_of_suppliers = User.objects.filter(subsidiary_id=request.user.subsidiary_id).count() 
    return render(request, 'supplier/company.html', {'subsidiary': subsidiary, 'num_of_suppliers': num_of_suppliers})


def my_offers(request):
    offers = Offer.objects.filter(supplier=request.user, is_accepted=False).all()
    for offer_temp in offers:
        if offer_temp.cash==offer_temp.ecocash==offer_temp.swipe==offer_temp.usd==False:
            offer_temp.no_payment = True
        if offer_temp.dipping_stick_available==offer_temp.meter_available==offer_temp.pump_available==False:
            offer_temp.no_equipments = True
        if not offer_temp.collection_address.strip():
            offer_temp.collection_address = f'N/A'
    return render(request, 'supplier/my_offers.html', {'offers':offers})


@login_required
def complete_transaction(request, id):
    transaction = Transaction.objects.filter(id = id).first()
    subsidiary_fuel = SubsidiaryFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).first()
    fuel_reserve = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id, payment_type = 'USD & RTGS').first()
    if transaction.offer.request.payment_method == 'USD':
        fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id, payment_type = 'USD').first()
    elif transaction.offer.request.payment_method == 'RTGS':
        fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id, payment_type = 'RTGS').first()
    fuel_type = transaction.offer.request.fuel_type.lower()
    if fuel_type == 'petrol':
        transaction_quantity = transaction.offer.quantity
        if fuel_reserve is not None:   
            available_fuel = fuel.petrol_quantity + fuel_reserve.petrol_quantity
        else:
            available_fuel = fuel.petrol_quantity
        if transaction_quantity <= available_fuel:
            transaction.is_complete = True
            transaction.save()
            if transaction_quantity > fuel.petrol_quantity:
                fuel_remainder = transaction_quantity - fuel.petrol_quantity
                fuel.petrol_quantity = 0
                fuel.save()
                fuel_reserve.petrol_quantity = fuel_reserve.petrol_quantity - fuel_remainder
                fuel_reserve.save()
            else:
                fuel.petrol_quantity = fuel.petrol_quantity - transaction_quantity
                fuel.save()

            subsidiary_fuel.petrol_quantity = subsidiary_fuel.petrol_quantity - transaction_quantity
            subsidiary_fuel.save()

            user = transaction.offer.request.name
            sord_update(request, user, transaction_quantity, 'SALE', 'Petrol')

            messages.success(request, "Transaction completed successfully!")
            return redirect('transaction')
        else:
            messages.warning(request, "There is not enough petrol in stock to complete the transaction.")
            return redirect('transaction')
    elif fuel_type == 'diesel':
        transaction_quantity = transaction.offer.quantity
        if fuel_reserve is not None:
            available_fuel = fuel.diesel_quantity + fuel_reserve.diesel_quantity
        else:
            available_fuel = fuel.diesel_quantity
        if transaction_quantity <= available_fuel:
            transaction.is_complete = True
            transaction.save()
            if transaction_quantity > fuel.diesel_quantity:
                fuel_remainder = transaction_quantity - fuel.diesel_quantity
                fuel.diesel_quantity = 0
                fuel.save()
                fuel_reserve.diesel_quantity = fuel_reserve.diesel_quantity - fuel_remainder
                fuel_request.save()
            else:
                fuel.diesel_quantity = fuel.diesel_quantity - transaction_quantity
                fuel.save()
            
            subsidiary_fuel.diesel_quantity = subsidiary_fuel.diesel_quantity - transaction_quantity
            subsidiary_fuel.save()

            user = transaction.offer.request.name
            sord_update(request, user, transaction_quantity, 'SALE', 'Diesel')

            messages.success(request, "Transaction completed successfully!")
            return redirect('transaction')
        else:
            messages.warning(request, "There is not enough diesel in stock to complete the transaction")
            return redirect('transaction')
    return render(request, 'supplier/transactions.html')


def invoice(request, id):
    
    buyer = request.user
    transactions = Transaction.objects.filter(buyer=buyer, id=id).first()
    
    context = {
        'transactions': transactions
    }
    pdf = render_to_pdf('supplier/invoice.html',context)
    return HttpResponse(pdf, content_type='application/pdf')


def view_invoice(request, id):
    transaction = Transaction.objects.filter(supplier=request.user, id=id).all()
    for transaction in transaction:
        subsidiary = Subsidiaries.objects.filter(id = transaction.supplier.subsidiary_id).first()
        if subsidiary is not None:
            transaction.depot = subsidiary.name
            transaction.address = subsidiary.address
    total = transaction.offer.quantity * transaction.offer.price
    g_total = total + 25
    
    context = {
        'transaction': transaction,
        'total': total,
        'g_total': g_total
    }
    return render(request, 'supplier/invoice2.html', context)


def sord_update(request, user, quantity, action, fuel_type, payment_type):
    end_quantity_zero =  SordSubsidiaryAuditTrail.objects.filter(subsidiary__id = request.user.subsidiary_id, fuel_type=fuel_type, payment_type=payment_type, end_quantity = 0).all()
    initial_sord = SordSubsidiaryAuditTrail.objects.filter(subsidiary__id = request.user.subsidiary_id, fuel_type=fuel_type, payment_type=payment_type).all()
    sord_quantity_zero = []
    sord_quantity = []
    for sord in end_quantity_zero:
        sord_quantity_zero.append(sord.sord_no)
    for x in initial_sord:
        if x.sord_no in sord_quantity_zero:
            pass
        else:
            sord_quantity.append(x)
    sord_quantity.sort(key = attrgetter('last_updated'), reverse = True)
    changing_quantity = quantity
    for entry in sord_quantity:
        if changing_quantity != 0:
            if entry.end_quantity < changing_quantity:
                new_sord_entry = SordSubsidiaryAuditTrail()
                new_sord_entry.sord_no = entry.sord_no
                new_sord_entry.action_no = entry.action_no + 1
                new_sord_entry.action = action
                new_sord_entry.initial_quantity = entry.end_quantity
                new_sord_entry.quantity_sold = entry.end_quantity
                new_sord_entry.end_quantity = 0
                new_sord_entry.received_by = user
                new_sord_entry.fuel_type = entry.fuel_type
                new_sord_entry.subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
                new_sord_entry.save()
                changing_quantity = changing_quantity - entry.end_quantity
            else:
                new_sord_entry = SordSubsidiaryAuditTrail()
                new_sord_entry.sord_no = entry.sord_no
                new_sord_entry.action_no = entry.action_no + 1
                new_sord_entry.action = action
                new_sord_entry.initial_quantity = entry.end_quantity
                new_sord_entry.quantity_sold = changing_quantity
                new_sord_entry.end_quantity = entry.end_quantity - changing_quantity
                new_sord_entry.received_by = user
                new_sord_entry.fuel_type = entry.fuel_type
                new_sord_entry.subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
                new_sord_entry.save()
                changing_quantity = 0

def view_confirmation_doc(request,id):
    delivery = DeliverySchedule.objects.filter(id=id).first()
    if delivery:
        filename = delivery.confirmation_document.name.split('/')[-1]
        response = HttpResponse(delivery.confirmation_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document Not Found')
        redirect('supplier:delivery_schedules')
    return response

def view_supplier_doc(request,id):
    delivery = DeliverySchedule.objects.filter(id=id).first()
    if delivery:
        filename = delivery.supplier_document.name.split('/')[-1]
        response = HttpResponse(delivery.supplier_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document Not Found')
        redirect('supplier:delivery_schedules')
    return response

def del_supplier_doc(request,id):
    delivery = DeliverySchedule.objects.filter(id=id).first()
    delivery.supplier_document = None
    delivery.save()
    messages.success(request, 'Document Removed Successfully')
    return redirect('supplier:delivery_schedules')

def view_delivery_schedule(request,id):
    if request.method == 'POST':
        supplier_document = request.FILES.get('supplier_document')
        delivery_id = request.POST.get('delivery_id')
        schedule = get_object_or_404(DeliverySchedule,id=delivery_id)
        schedule.supplier_document = supplier_document
        schedule.save()
        messages.success(request, "File Successfully Uploaded")
        msg = f"Delivery Confirmed for {schedule.transaction.buyer.company}, Click To View Confirmation Document"
        Notification.objects.create(user=request.user,action='DELIVERY', message=msg, reference_id=schedule.id)
        return redirect('delivery_schedules')
    schedule = DeliverySchedule.objects.filter(id=id).first()
    if schedule.transaction.offer.delivery_method.lower() == 'delivery':
        schedule.delivery_address = schedule.transaction.offer.request.delivery_address
    else:
        schedule.delivery_address = schedule.transaction.offer.collection_address
    return render(request, 'supplier/view_delivery_schedule.html', {'schedule': schedule})
    
