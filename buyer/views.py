import secrets
from datetime import datetime

import requests
from django.contrib import messages
from django.contrib.auth import (authenticate, get_user_model, login, logout, update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.db.models import Q
from django.shortcuts import redirect, render
from django.http import HttpResponse
from buyer.models import User
from buyer.recommend import recommend
from company.models import Company, FuelUpdate
from supplier.models import Offer, Subsidiaries, Transaction

from .constants import sample_data
from .forms import (BuyerRegisterForm, BuyerUpdateForm, FuelRequestForm,
                    PasswordChangeForm)
from .models import FuelRequest
from buyer.utils import render_to_pdf



user = get_user_model()

def login_success(request):
    """
    Redirects users based on whether they are in which group
    """
    user_type  = request.user.user_type
    print(user_type)
    if user_type == "BUYER":
        return redirect("buyer-dashboard")
    elif user_type == 'SS_SUPPLIER':
        return redirect("serviceStation:home")
    elif user_type == 'SUPPLIER':
        return redirect("fuel-request")    
    elif user_type == 'S_ADMIN':
        return redirect("users:allocate")
    else:
        return redirect("users:suppliers_list")
def token_is_send(request, user):
    token = secrets.token_hex(12)
    domain = request.get_host()            
    url = f'{domain}/verification/{token}/{user.id}'
    sender = "intelliwhatsappbanking@gmail.com"
    subject = 'Fuel Finder Registration'
    message = f"Dear {user.first_name}  {user.last_name}, please complete signup here : \n {url} \n. "            
    try:
        print(message)
        msg = EmailMultiAlternatives(subject, message, sender, [f'{user.email}'])
        msg.send()

        messages.success(request, f"{user.first_name}  {user.last_name} Registered Successfully")
        return True
    except Exception as e:
        print(e)
        messages.warning(request, f"Oops , Something Wen't Wrong, Please Try Again")
        return False              
    messages.success(request, ('Your profile was successfully updated!'))
    return render(request, 'buyer/send_email.html')

# Create your views here.
def register(request):
    if request.method == 'POST':
        form = BuyerRegisterForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            full_name = first_name + " " + last_name
            i = 0
            username = initial_username = first_name[0] + last_name
            while  User.objects.filter(username=username.lower()).exists():
                username = initial_username + str(i) 
                i+=1
            user = User.objects.create(email=email, username=username.lower(),  phone_number=phone_number, first_name=first_name, last_name=last_name, is_active=False)        
            if token_is_send(request, user):
                messages.success(request, f"{full_name} Registered Successfully")   
                if user.is_active:
                    send_message(user.phone_number, "You have been registered succesfully")
                    user.stage = 'requesting'
                    user.save()               
                return render(request, 'buyer/send_email.html')
            else:
                messages.warning(request, f"Oops , Something Wen't Wrong, Please Try Again")
                return render(request, 'buyer/send_email.html')
        
        else:
            msg = "Error in Information Submitted"
            messages.error(request, msg)

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}')
            return redirect('buyer-login')
    else:
        form = BuyerRegisterForm
    
    return render(request, 'buyer/signup.html', {'form': form})

def send_message(phone_number, message):
    payload = {
        "phone": phone_number,
        "body": message
    }
    url = "https://eu33.chat-api.com/instance78632/sendMessage?token=sq0pk8hw4iclh42b"
    r = requests.post(url=url, data=payload)
    print(r)
    return r.status_code

@login_required
def profile(request):
    if request.method == 'POST':
        old = request.POST.get('old_password')
        new1 = request.POST.get('new_password1')
        new2 = request.POST.get('new_password2')

        if authenticate(request, username=request.user.username, password=old):
            if new1 != new2:
                messages.warning(request, "Passwords Don't Match")
                return redirect('buyer-profile')
            else:
                user = request.user
                user.set_password(new1)
                user.save()
                update_session_auth_hash(request, user)

                messages.success(request, 'Password Successfully Changed')
                return redirect('buyer-profile')
        else:
            messages.warning(request, 'Wrong Old Password, Please Try Again')
            return redirect('buyer-profile')

    context = {
        'form': PasswordChangeForm(user=request.user),
        'user_logged': request.user,
    }
    return render(request, 'buyer/profile.html', context)

#@login_required
def fuel_request(request):
    user_logged = request.user
    fuel_requests = FuelRequest.objects.filter(name=user_logged, is_complete=False).all()
    for fuel_request in fuel_requests:
        if fuel_request.is_direct_deal:
            search_company = FuelUpdate.objects.filter(id= fuel_request.last_deal).first()
            depot = Subsidiaries.objects.filter(id=search_company.relationship_id).first()
            company = Company.objects.filter(id= search_company.company_id).first()
            fuel_request.request_company = company.name
            fuel_request.depot = depot.name
        else:
            fuel_request.request_company = ''
    # print(fuel_requests)
    for fuel_request in fuel_requests:
        offer = Offer.objects.filter(request=fuel_request).first()
        if offer is not None:
            fuel_request.has_offers = True
        else:
            fuel_request.has_offers = False

    context = {
        'fuel_requests' : fuel_requests
        } 

    return render(request, 'buyer/fuel_request.html', context=context)

def fuel_finder(request):
    if request.method == 'POST':
        form = FuelRequestForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']
            delivery_method = form.cleaned_data['delivery_method']
            fuel_type = form.cleaned_data['fuel_type']
            print(f"===================={request.POST.get('company_id')}--------------------  ")
            fuel_request = FuelRequest()
            fuel_request.name = request.user       
            fuel_request.amount = amount
            fuel_request.fuel_type = fuel_type
            fuel_request.payment_method = payment_method
            fuel_request.delivery_method = delivery_method
            fuel_request.wait = True
            fuel_request.save()

            
            messages.success(request, f'kindly not your request has been made ')
    else:
        form = FuelRequestForm
    return render(request, 'buyer/dashboard.html',{'form':form, 'sample_data':sample_data})


def dashboard(request):
    updates = FuelUpdate.objects.filter(sub_type="Depot").filter(~Q(diesel_quantity=0.00)).filter(~Q(petrol_quantity=0.00))
    for update in updates:
        subsidiary = Subsidiaries.objects.filter(id = update.relationship_id).first()
        company = Company.objects.filter(id=update.company_id).first()
        if company is not None:
            update.company = company.name
            update.depot = subsidiary.name
            update.address = subsidiary.address
    if request.method == 'POST':
        form = FuelRequestForm(request.POST)
        if 'MakeDeal' in request.POST:
            if form.is_valid():     
                fuel_request = FuelRequest()

                fuel_request.name = request.user       
                fuel_request.amount = form.cleaned_data['amount']
                fuel_request.fuel_type = form.cleaned_data['fuel_type']
                fuel_request.usd = True if request.POST.get('usd') == "True" else False
                fuel_request.cash = True if request.POST.get('cash') == "True" else False
                fuel_request.ecocash = True if request.POST.get('ecocash') == "True" else False
                fuel_request.swipe = True if request.POST.get('swipe') == "True" else False
                fuel_request.delivery_method = form.cleaned_data['delivery_method']
                fuel_request.delivery_address = request.POST.get('s_number') + " " + request.POST.get('s_name') + " " + request.POST.get('s_town')
                fuel_request.storage_tanks = True if request.POST.get('storage_tanks') == "True" else False
                fuel_request.pump_required = True if request.POST.get('pump_required') == "True" else False
                fuel_request.dipping_stick_required = True if request.POST.get('usd') == "True" else False
                fuel_request.meter_required = True if request.POST.get('usd') == "True" else False
                fuel_request.is_direct_deal = True
                fuel_request.last_deal = request.POST.get('company_id')
                print(fuel_request.last_deal)
                fuel_request.save()
            messages.success(request, f'kindly not your request has been made ')

        if 'WaitForOffer' in request.POST:
            if form.is_valid():
                fuel_request = FuelRequest()
                fuel_request.name = request.user       
                fuel_request.amount = form.cleaned_data['amount']
                fuel_request.fuel_type = form.cleaned_data['fuel_type']
                fuel_request.usd = True if request.POST.get('usd') == "True" else False
                fuel_request.cash = True if request.POST.get('cash') == "True" else False
                fuel_request.ecocash = True if request.POST.get('ecocash') == "True" else False
                fuel_request.swipe = True if request.POST.get('swipe') == "True" else False
                fuel_request.delivery_method = form.cleaned_data['delivery_method']
                fuel_request.delivery_address = request.POST.get('s_number') + " " + request.POST.get('s_name') + " " + request.POST.get('s_town')
                fuel_request.storage_tanks = True if request.POST.get('storage_tanks') == "True" else False
                fuel_request.pump_required = True if request.POST.get('pump_required') == "True" else False
                fuel_request.dipping_stick_required = True if request.POST.get('usd') == "True" else False
                fuel_request.meter_required = True if request.POST.get('usd') == "True" else False
                fuel_request.wait = True
                fuel_request.save()
            messages.success(request, f'Fuel Request has been submitted succesfully and now waiting for an offer')

        if 'Recommender' in request.POST:
            if form.is_valid():
                amount = form.cleaned_data['amount']
                delivery_method = form.cleaned_data['delivery_method']
                fuel_type = form.cleaned_data['fuel_type']
                fuel_request = FuelRequest()
                fuel_request.name = request.user       
                fuel_request.amount = amount
                fuel_request.fuel_type = fuel_type
                fuel_request.delivery_method = delivery_method
                fuel_request.save()
                offer_id, response_message = recommend(fuel_request)
                if not offer_id:
                    messages.error(request,response_message)                    
                else:
                    offer = Offer.objects.filter(id=offer_id).first()
                    messages.info(request, "Match Found")
                    return render(request, 'buyer/dashboard.html',{'form':form, 'updates': updates, 'offer': offer})                
    else:
        form = FuelRequestForm     
    return render(request, 'buyer/dashboard.html',{'form':form, 'updates': updates})



def offers(request, id):
    selected_request = FuelRequest.objects.filter(id=id).first()
    offers = Offer.objects.filter(request=selected_request).filter(declined=False).all()
    buyer = request.user 
    for offer in offers:
        depot = Subsidiaries.objects.filter(id=offer.supplier.subsidiary_id).first()
        offer.depot_name = depot.name
   
    return render(request, 'buyer/offer.html', {'offers': offers })


def accept_offer(request, id):    
    offer = Offer.objects.filter(id=id).first()
    print(offer.supplier)  
    Transaction.objects.create(offer=offer, buyer=request.user, supplier=offer.supplier)  
    FuelRequest.objects.filter(id=offer.request.id).update(is_complete=True)
    return redirect("buyer-fuel-request")

def reject_offer(request, id):    
    offer = Offer.objects.filter(id=id).first()
    offer.declined = True
    offer.save()
    my_request = FuelRequest.objects.filter(id = offer.request.id).first()
    my_request.wait = True
    my_request.is_complete = False
    my_request.save()     
    # FuelRequest.objects.filter(id=offer.request.id).update(is_complete=True)
    messages.success(request, "Your request has been saved and as offer updates are coming you will receive notifications")
    return redirect("buyer-fuel-request")


def transactions(request):
    buyer = request.user
    transactions = Transaction.objects.filter(buyer=buyer).all()
    context = {
        'transactions': transactions
    }

    return render(request, 'buyer/transactions.html', context=context)

def invoice(request):
    buyer = request.user
    transactions = Transaction.objects.filter(buyer=buyer).all()
    context = {
        'transactions': transactions
    }
    pdf = render_to_pdf('buyer/invoice.html',context)
    return HttpResponse(pdf, content_type='application/pdf')

    
