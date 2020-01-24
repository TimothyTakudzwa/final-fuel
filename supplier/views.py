from itertools import chain
from operator import attrgetter

from django.contrib.auth import authenticate, update_session_auth_hash, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.contrib import messages

import secrets
from users.models import Audit_Trail
from datetime import date, time
from buyer.constants2 import industries, job_titles
from buyer.forms import BuyerUpdateForm
from buyer.models import Company
from users.models import AuditTrail
from .forms import PasswordChange, RegistrationForm, \
    RegistrationEmailForm, UserUpdateForm, FuelRequestForm, CreateCompany, OfferForm
from .models import FuelRequest, Transaction, TokenAuthentication, Offer, Subsidiaries, FuelAllocation
from company.models import Company, FuelUpdate
from notification.models import Notification
from django.contrib.auth import get_user_model
from whatsapp.helper_functions import send_message

User = get_user_model()

# today's date
today = date.today()


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
    return render(request, 'supplier/user_profile.html')


@login_required()
def fuel_request(request):
    requests = FuelRequest.objects.filter(is_deleted=False ,wait=True, is_complete=False).all()
    direct_requests =  FuelRequest.objects.filter(is_deleted=False, is_complete=False, is_direct_deal=True, last_deal=request.user.subsidiary_id).all()
    requests = list(chain(requests, direct_requests))
    requests.sort(key = attrgetter('date', 'time'), reverse = True)

    for buyer_request in requests:
        if buyer_request.payment_method == 'USD':
            fuel = FuelUpdate.objects.filter(relationship_id=request.user.subsidiary_id).filter(entry_type='USD').first()
        elif buyer_request.payment_method == 'RTGS':
            fuel = FuelUpdate.objects.filter(relationship_id=request.user.subsidiary_id).filter(entry_type='RTGS').first()
        elif buyer_request.payment_method == 'USD & RTGS':
            fuel = FuelUpdate.objects.filter(relationship_id=request.user.subsidiary_id).filter(entry_type='USD & RTGS').first()
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
    return render(request, 'supplier/fuel_request.html', {'requests':requests})

def new_fuel_request(request, id):
    requests = FuelRequest.objects.filter(id = id,wait=True).all()
    print(requests)
    return render(request, 'supplier/new_fuel_request.html', {'requests':requests})

def accepted_offer(request, id):
    transactions = Transaction.objects.filter(id=id).all()
    return render(request, 'supplier/new_transaction.html', {'transactions':transactions})

def rejected_offer(request, id):
    offers = Offer.objects.filter(id=id).all()
    return render(request, 'supplier/my_offer.html', {'offers':offers})



@login_required
def available_stock(request):
    updates = FuelUpdate.objects.filter(sub_type='Suballocation', relationship_id=request.user.subsidiary_id).all()

    return render(request, 'supplier/available_fuel.html', {'updates': updates})

@login_required()
def stock_update(request,id):
    updates = FuelUpdate.objects.filter(sub_type='Suballocation', id=id).first()
    available_petrol = updates.petrol_quantity
    available_diesel = updates.diesel_quantity
    if request.method == 'POST':
        if FuelUpdate.objects.filter(id=id).exists():
            fuel_update = FuelUpdate.objects.filter(id=id).first()
            if request.POST['fuel_type'] == 'Petrol':
                if int(request.POST['quantity']) > available_petrol:
                    messages.warning(request, 'You can only reduce your petrol quantity')
                    return redirect('available_stock')
                fuel_update.petrol_quantity = int(request.POST['quantity'])
            else:
                if int(request.POST['quantity']) > available_diesel:
                    messages.warning(request, 'You can only reduce your diesel quantity')
                    return redirect('available_stock')
                fuel_update.diesel_quantity = int(request.POST['quantity'])
            fuel_update.cash = request.POST['cash']
            fuel_update.swipe = request.POST['swipe']
            if fuel_update.entry_type != 'USD':
                fuel_update.ecocash = request.POST['ecocash']
            fuel_update.save()
            messages.success(request, 'Fuel successfully updated')
    return redirect('available_stock')


def offer(request, id):
    form = OfferForm(request.POST)
    if request.method == "POST":
        print(f"---------price : {request.POST.get('price')}------------")
        if float(request.POST.get('price')) != 0 and float(request.POST.get('quantity')) != 0:
            fuel_request = FuelRequest.objects.get(id=id)
            fuel = FuelUpdate.objects.filter(relationship_id=request.user.subsidiary_id).first()
            subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
            
            if fuel_request.fuel_type.lower() == 'petrol':
                available_fuel = fuel.petrol_quantity
            elif fuel_request.fuel_type.lower() == 'diesel':
                available_fuel = fuel.diesel_quantity
            offer_quantity = int(request.POST.get('quantity'))
            amount = fuel_request.amount

            if offer_quantity <= available_fuel:
                if offer_quantity <= amount:
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

                    message = f'You have a new offer of {offer_quantity}L {fuel_request.fuel_type.lower()} at ${offer.price} from {request.user.first_name} {request.user.last_name} for your request of {fuel_request.amount}L'
                    Notification.objects.create(message = message, user = fuel_request.name, reference_id = offer.id, action = "new_offer")
                    click_url = f'https://fuelfinderzim.com/new_fuel_offer/{offer.id}'
                    if offer.request.name.activated_for_whatsapp:
                        send_message(offer.request.name.phone_number,f'Your have received a new offer of {offer_quantity}L {fuel_request.fuel_type.lower()} at ${offer.price} from {request.user.first_name} {request.user.last_name} for your request of {fuel_request.amount}L click {click_url} to view details')
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
    if request.method == 'POST':
        fuel = FuelUpdate.objects.filter(relationship_id=request.user.subsidiary_id).first()
        subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
        
        if offer.request.fuel_type.lower() == 'petrol':
            available_fuel = fuel.petrol_quantity
        elif offer.request.fuel_type.lower() == 'diesel':
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
                message = f'You have an updated offer of {new_offer}L {offer.request.fuel_type.lower()} at ${offer.price} from {request.user.company.name.title()} {request.user.last_name} for your request of {offer.request.amount}L'
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
    context= { 
       'transactions' : Transaction.objects.filter(supplier=request.user).all()
        }
    return render(request, 'supplier/transactions.html',context=context)


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
                print(user)
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
                        # selected_company = Company.objects.create(name=request.POST.get('company'))
                        selected_company.save()
                        user.company = selected_company
                        user.is_waiting = True
                        user.save() 
                        TokenAuthentication.objects.filter(user=user).update(used=True)
                        print("i am here")
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
    print(id)
    form = CreateCompany()
    user = User.objects.filter(id=id).first()
    print(user.company)
    user_type = user.user_type
    print(user_type)
    form.initial['company_name'] = user.company.name

    if request.method == 'POST':
        form = CreateCompany(request.POST)
        if form.is_valid():
            if user_type == 'BUYER':
                company_name = request.POST.get('company_name')
                address = request.POST.get('address')
                logo = request.FILES.get('logo')
                company_name = user.company.name
                Company.objects.filter(name=company_name).update(name = company_name,
                address = address, logo = logo)
                return redirect('login')

            else:
                company_name = request.POST.get('company_name')
                address = request.POST.get('address')
                logo = request.FILES.get('logo')
                iban_number = request.POST.get('iban_number')
                license_number = request.POST.get('license_number')
                Company.objects.filter(name=company_name).update(name = company_name,
                address = address, logo = logo, iban_number = iban_number, license_number = license_number)
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
