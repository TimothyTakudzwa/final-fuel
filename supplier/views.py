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
    return render(request, 'supplier/accounts/change_password.html', context=context)


@login_required()
def account(request):
    context = {
        'title': 'Fuel Finder | Account',
        'user': UserUpdateForm(instance=request.user)

    }
    return render(request, 'supplier/accounts/account.html', context=context)


@login_required()
def fuel_request(request):
    requests = FuelRequest.objects.filter(date=today)
    fuel = FuelUpdate.objects.filter(relationship_id=request.user.id).first()
    for buyer_request in requests:
        if Offer.objects.filter(supplier_id=request.user, request_id=buyer_request).exists():
            offer = Offer.objects.filter(supplier_id=request.user, request_id=buyer_request).first()
            buyer_request.my_offer = f'{offer.quantity}ltrs @ ${offer.price}'
            buyer_request.offer_price = offer.price
            buyer_request.offer_quantity = offer.quantity
            buyer_request.offer_id = offer.id
        else:
            buyer_request.my_offer = 0
            buyer_request.offer_id = 0
        if fuel:
            if buyer_request.fuel_type == 'petrol':
                buyer_request.price = fuel.petrol_price
            else:
                buyer_request.price = fuel.diesel_price
        else:
            buyer_request.price = 0
    return render(request, 'supplier/accounts/fuel_request.html', {'requests':requests})


@login_required()
def rate_supplier(request):
    context = {
        'title': 'Fuel Finder | Rate Supplier',
    }
    return render(request, 'supplier/accounts/ratings.html', context=context)


@login_required
def fuel_update(request):

    updates = FuelUpdate.objects.filter(relationship_id=request.user.subsidiary_id).first()
    subsidiary_name = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
    if request.method == 'POST':
        if FuelUpdate.objects.filter(relationship_id=request.user.subsidiary_id).exists():
            fuel_update = FuelUpdate.objects.get(relationship_id=request.user.subsidiary_id)
            fuel_update.petrol_quantity = request.POST['petrol_quantity']
            fuel_update.petrol_price = request.POST['petrol_price']
            fuel_update.diesel_quantity = request.POST['diesel_quantity']
            fuel_update.diesel_price = request.POST['diesel_price']
            fuel_update.cash = request.POST['cash']
            fuel_update.ecocash = request.POST['ecocash']
            fuel_update.swipe = request.POST['swipe']
            fuel_update.usd = request.POST['usd']
            fuel_update.save()
            messages.success(request, 'updated quantities successfully')
            service_station = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
            reference = 'fuel quantity updates'
            reference_id = fuel_update.id
            action = f"{request.user.username} has made an update of diesel quantity to {fuel_update.diesel_quantity}L @ {fuel_update.diesel_price} and petrol quantity to {fuel_update.petrol_quantity}L @ {fuel_update.petrol_price}"
            Audit_Trail.objects.create(company=request.user.company,service_station=service_station,user=request.user,action=action,reference=reference,reference_id=reference_id)
            return redirect('fuel_update')
        else:
            sub_type = 'Depot'
            petrol_quantity = request.POST.get('petrol_quantity')
            petrol_price = request.POST.get('petrol_price')
            diesel_quantity = request.POST.get('diesel_quantity')
            diesel_price = request.POST.get('diesel_price')
            fuel_update.cash = request.POST['cash']
            fuel_update.ecocash = request.POST['ecocash']
            fuel_update.swipe = request.POST['swipe']
            fuel_update.usd = request.POST['usd']
            relationship_id = request.user.subsidiary_id
            FuelUpdate.objects.create(relationship_id=relationship_id, sub_type=sub_type, petrol_quantity=petrol_quantity, petrol_price=petrol_price, diesel_quantity=diesel_quantity, diesel_price=diesel_price)
            messages.success(request, 'Quantities uploaded successfully')
            return redirect('fuel_update')

    return render(request, 'supplier/accounts/stock.html', {'updates': updates, 'subsidiary': subsidiary_name.name})


def offer(request, id):
    form = OfferForm(request.POST)
    if request.method == "POST":
        fuel_request = FuelRequest.objects.get(id=id)

        offer = int(request.POST.get('quantity'))
        amount = fuel_request.amount

        if offer <= amount:
            offer = Offer()
            offer.supplier = request.user
            offer.request = fuel_request
            offer.price = request.POST.get('price')      
            offer.quantity = request.POST.get('quantity')
            offer.fuel_type = request.POST.get('fuel_type')
            offer.usd = True if request.POST.get('usd') == "True" else False
            offer.cash = True if request.POST.get('cash') == "True" else False
            offer.ecocash = True if request.POST.get('ecocash') == "True" else False
            offer.swipe = True if request.POST.get('swipe') == "True" else False
            offer.delivery_method = request.POST.get('delivery_method')
            offer.collection_address = request.POST.get('s_number') + " " + request.POST.get('s_name') + " " + request.POST.get('s_town')
            offer.pump_available = True if request.POST.get('pump_required') == "True" else False
            offer.dipping_stick_available = True if request.POST.get('usd') == "True" else False
            offer.meter_available = True if request.POST.get('usd') == "True" else False
            offer.save()
            
            messages.success(request, 'Offer uploaded successfully')
            action = f"{request.user}  made an offer of {offer}L @ {request.POST.get('price')} to a request made by {fuel_request.name.username}"
            service_station = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
            reference = 'offers'
            reference_id = fuel_request.id
            Audit_Trail.objects.create(company=request.user.company,service_station=service_station,user=request.user,action=action,reference=reference,reference_id=reference_id)
            return redirect('fuel-request')
        else:
            messages.warning(request, 'You can not make an offer greater than the requested fuel quantity!')
            return redirect('fuel-request')
    return render(request, 'supplier/accounts/fuel_request.html')

@login_required
def edit_offer(request, id):
    offer = Offer.objects.get(id=id)
    if request.method == 'POST':
        new_offer = int(request.POST.get('quantity'))
        request_quantity = offer.request.amount
        if new_offer <= request_quantity:
            offer.price = request.POST.get('price')      
            offer.quantity = request.POST.get('quantity')
            offer.usd = True if request.POST.get('usd') == "True" else False
            offer.cash = True if request.POST.get('cash') == "True" else False
            offer.ecocash = True if request.POST.get('ecocash') == "True" else False
            offer.swipe = True if request.POST.get('swipe') == "True" else False
            offer.delivery_method = request.POST.get('delivery_method1')
            offer.collection_address = request.POST.get('s_number') + " " + request.POST.get('s_name') + " " + request.POST.get('s_town')
            offer.pump_available = True if request.POST.get('pump_required') == "True" else False
            offer.dipping_stick_available = True if request.POST.get('usd') == "True" else False
            offer.meter_available = True if request.POST.get('usd') == "True" else False
            offer.save()
            messages.success(request, 'Offer successfully updated')
            return redirect('fuel-request')
        else:
            messages.warning(request, 'You can not make an offer greater than the requested fuel quantity!')
            return redirect('fuel-request')
    return render(request, 'supplier/accounts/fuel_request.html', {'offer': offer})


@login_required
def transaction(request):
    context= { 
       'transactions' : Transaction.objects.filter(supplier=request.user).all()
        }
    return render(request, 'supplier/accounts/transactions.html',context=context)

@login_required
def complete_transaction(request, id):
    transaction = Transaction.objects.get(id=id)
    transaction.complete == True
    transaction.save()
    messages.success(request, 'Transaction completed successfully')
    return redirect('transaction')


@login_required()
def notifications(request):
    context = {
        'title': 'Fuel Finder | Notification',
        'notifications': Notification.objects.filter(user=request.user),
        'notifications_count': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    msgs = Notification.objects.filter(user=request.user, is_read=False)
    if msgs.exists():
        nots = Notification.objects.filter(user=request.user, is_read=False)
        for i in nots:
            user_not = Notification.objects.get(user=request.user, id=i.id)
            user_not.is_read = True
            user_not.save()
    return render(request, 'supplier/accounts/notifications.html', context=context)


def allocated_quantity(request):
    allocations = FuelAllocation.objects.filter(assigned_staff_id= request.user.subsidiary_id).all()
    return render(request, 'supplier/accounts/allocated_quantity.html', {'allocations': allocations})


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
    form = BuyerUpdateForm
    context = {
        'title': 'Fuel Finder | Verification',
        'form' : form
    }
    check = User.objects.filter(id=user_id)
    print("here l am ")

    if check.exists():
        user = User.objects.get(id=user_id)
        print(user)
        if user.user_type == 'BUYER':
            companies = Company.objects.filter(company_type='CORPORATE').all()
        else:
            companies = Company.objects.filter(company_type='SUPPLIER').all()
        
        token_check = TokenAuthentication.objects.filter(user=user, token=token)
        result = bool([token_check])
        print(result)
        if result == True:
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
                        user.save()
                        print("i am here")

                    else:
                        selected_company =Company.objects.create(name=request.POST.get('company'))
                        user.is_active = False
                        user.is_waiting = True
                        selected_company = Company.objects.create(name=request.POST.get('company'))
                        selected_company.save()
                        user.company = selected_company
                        user.save() 
                        print("i am here")
                        return redirect('supplier:create_company', id=user.id)
                    
            else:
               
                return render(request, 'supplier/accounts/verify.html', {'form': form, 'industries': industries, 'companies': companies, 'jobs': job_titles})
        else:
            messages.warning(request, 'Wrong verification token')
            return redirect('login')
    else:
        messages.warning(request, 'Wrong verification id')
        return redirect('login')
    
    return render(request, 'supplier/accounts/verify.html', {'form': form, 'industries': industries, 'companies': companies, 'jobs': job_titles})

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
        print("inside post")
        print(form.errors)
        if form.is_valid():
            print('inside form valid')
            if user_type == 'BUYER':
                print("hezvo tapinda mubyer")
                company_name = request.POST.get('company_name')
                address = request.POST.get('address')
                logo = request.FILES.get('logo')
                company_name = user.company.name
                Company.objects.filter(name=company_name).update(name = company_name,
                address = address, logo = logo)
                print("l have updated the buyer company")

            else:
                company_name = request.POST.get('company_name')
                address = request.POST.get('address')
                logo = request.FILES.get('logo')
                iban_number = request.POST.get('iban_number')
                license_number = request.POST.get('license_number')
                Company.objects.filter(name=company_name).update(name = company_name,
                address = address, logo = logo, iban_number = iban_number, license_number = license_number)
                print("l have saved the supplier company")
            return redirect('home')
    return render(request, 'supplier/accounts/create_company.html', {'form': form, 'user_type':user_type })

    
def company(request):
    compan = Company.objects.filter(id = request.user.company.id).first()
    num_of_subsidiaries = Subsidiaries.objects.filter(company=request.user.company).count()
    fuel_capacity = FuelUpdate.objects.filter(company_id=request.user.company.id).first()   
    return render(request, 'supplier/accounts/company.html', {'compan': compan, 'num_of_subsidiaries': num_of_subsidiaries, 'fuel_capacity': fuel_capacity})


def my_offers(request):
    offers = Offer.objects.filter(supplier=request.user).all()
    return render(request, 'supplier/accounts/my_offers.html', {'offers':offers})