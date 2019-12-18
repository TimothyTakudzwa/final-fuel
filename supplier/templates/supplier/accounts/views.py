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
    return render(request, 'supplier/accounts/change_password.html', context=context)


@login_required()
def account(request):
    context = {
        'title': 'Fuel Finder | Account',
        'user': UserUpdateForm(instance=request.user)

    }
    user = request.user
    if request.method == 'POST':
        try:
            phone_number = int(request.POST.get('phone_number'))
            if len(str(phone_number)) == 12 and int(str(phone_number)[:4]) == 2637:
                user.phone_number = phone_number
                user.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('account')
            else:
                messages.warning(request, "Wrong phone number format! Please re-enter the phone number")
                return redirect('account')
        except:
            messages.warning(request, 'Phone number can only contain numbers!')
            return redirect('account')
    return render(request, 'supplier/accounts/account.html', context=context)


@login_required()
def fuel_request(request):
    requests = FuelRequest.objects.filter(is_deleted=False ,wait=True).all()
    fuel = FuelUpdate.objects.filter(relationship_id=request.user.id).first()
    for buyer_request in requests:
        if buyer_request.dipping_stick_required==buyer_request.meter_required==buyer_request.pump_required==False:
            buyer_request.equipments = f'No Equipment Required'
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
        petrol_update = float(request.POST['petrol_quantity'])
        diesel_update = float(request.POST['diesel_quantity'])
        if FuelUpdate.objects.filter(relationship_id=request.user.subsidiary_id).exists():
            fuel_update = FuelUpdate.objects.get(relationship_id=request.user.subsidiary_id)
            petrol_available = fuel_update.petrol_quantity
            diesel_available = fuel_update.diesel_quantity
            if petrol_update < petrol_available and diesel_update < diesel_available:
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
                messages.warning(request, 'You can only reduce your current stocks not increase')
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
    if request.method == "POST" and float(request.POST.get('price')) != 0 and float(request.POST.get('quantity')) != 0:
        fuel_request = FuelRequest.objects.get(id=id)
        fuel = FuelUpdate.objects.filter(relationship_id=request.user.subsidiary_id).first()
        
        if fuel_request.fuel_type.lower() == 'petrol':
            available_fuel = fuel.petrol_quantity
        elif fuel_request.fuel_type.lower() == 'diesel':
            available_fuel = fuel_request.diesel_quantity
        offer = int(request.POST.get('quantity'))
        amount = fuel_request.amount

        if offer <= available_fuel:
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
        else:
            messages.warning(request, 'You can not offer fuel more than the available fuel stock')
            return redirect('fuel-request')
    else:
        messages.warning(request, "Please fill all required fields to complete an offer")
        return redirect('fuel-request')
    return render(request, 'supplier/accounts/fuel_request.html')

@login_required
def edit_offer(request, id):
    offer = Offer.objects.get(id=id)
    if request.method == 'POST':
        fuel = FuelUpdate.objects.filter(relationship_id=request.user.subsidiary_id).first()
        
        if fuel_request.fuel_type.lower() == 'petrol':
            available_fuel = fuel.petrol_quantity
        elif fuel_request.fuel_type.lower() == 'diesel':
            available_fuel = fuel_request.diesel_quantity
        new_offer = int(request.POST.get('quantity'))
        request_quantity = offer.request.amount

        if new_offer <= available_fuel:
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
        else:
            messages.warning(request, 'You can not offer fuel more than the available fuel stock')
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
                        user.is_waiting = True
                        user.save()
                        TokenAuthentication.objects.filter(user=user).update(used=True)
                        my_admin = User.objects.filter(company=selected_company,user_type='S_ADMIN').first()
                        if my_admin is not None:
                            return render(request,'supplier/final_registration.html',{'my_admin': my_admin})
                        else:
                            return render(request,'supplier/final_reg.html')

                    else:
                        selected_company =Company.objects.create(name=request.POST.get('company'))
                        user.is_active = False
                        user.is_waiting = True
                        selected_company = Company.objects.create(name=request.POST.get('company'))
                        selected_company.save()
                        user.company = selected_company
                        user.is_waiting = True
                        user.save() 
                        TokenAuthentication.objects.filter(user=user).update(used=True)
                        print("i am here")
                        return redirect('supplier:create_company', id=user.id)
                    
            else:
                return render(request, 'supplier/accounts/verify.html', {'form': form, 'industries': industries, 'companies': companies, 'jobs': job_titles})
        else:
            messages.warning(request, 'This link has been used before')
            return redirect('buyer-register')
        
    else:
        messages.warning(request, 'Wrong verification token, kindly follow the link send in the email')
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
        if form.is_valid():
            if user_type == 'BUYER':
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
            return redirect('login')
    return render(request, 'supplier/accounts/create_company.html', {'form': form, 'user_type':user_type })

    
def company(request):
    compan = Company.objects.filter(id = request.user.company.id).first()
    num_of_subsidiaries = Subsidiaries.objects.filter(company=request.user.company).count()
    fuel_capacity = FuelUpdate.objects.filter(company_id=request.user.company.id).first()   
    return render(request, 'supplier/accounts/company.html', {'compan': compan, 'num_of_subsidiaries': num_of_subsidiaries, 'fuel_capacity': fuel_capacity})


def my_offers(request):
    offers = Offer.objects.filter(supplier=request.user).all()
    return render(request, 'supplier/accounts/my_offers.html', {'offers':offers})


def invoice(request, id):
    
    buyer = request.user
    transactions = Transaction.objects.filter(buyer=buyer, id=id).first()
    
    context = {
        'transactions': transactions
    }
    pdf = render_to_pdf('supplier/accounts/invoice.html',context)
    return HttpResponse(pdf, content_type='application/pdf')


def view_invoice(request, id):
    transaction = Transaction.objects.filter(supplier=request.user, id=id).all()
    for transaction in transaction:
        subsidiary = Subsidiaries.objects.filter(id = transaction.supplier.subsidiary_id).first()
        if subsidiary is not None:
            transaction.depot = subsidiary.name
            transaction.address = subsidiary.address
    total = transaction.offer.quantity + transaction.offer.price
    g_total = total + 25
    
    context = {
        'transaction': transaction,
        'total': total,
        'g_total': g_total
    }
    return render(request, 'supplier/accounts/invoice2.html', context)
