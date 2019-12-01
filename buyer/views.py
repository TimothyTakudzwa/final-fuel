from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, update_session_auth_hash, login, logout
from .forms import BuyerRegisterForm, BuyerUpdateForm, FuelRequestForm, PasswordChangeForm
#from supplier.forms import FuelRequestForm
from .constants import sample_data
from buyer.models import User
from company.models import Company, FuelUpdate
import requests
import secrets
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from datetime import datetime
#from .constants import sender, subject
from .models import FuelRequest
from supplier.models import Offer
from django.contrib.auth import get_user_model

user = get_user_model()

# def login_success(request):
#     """
#     Redirects users based on whether they are in the admins group
#     """
#     if request.user(user_type="buyer").exists():
#         # user is an admin
#         return redirect("buyer-profile")
#     else:
#         return redirect("other_view")

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
    else:
        return redirect("users:suppliers_list")
def token_is_send(request, user):
    token = secrets.token_hex(12)
    domain = request.get_host()            
    url = f'{domain}/verification/{token}/{user.id}'
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
    
    return render(request, 'buyer/register.html', {'form': form})

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
    fuel_requests = FuelRequest.objects.filter(name=user_logged, is_closed=False).all()
    for fuel_request in fuel_requests:
        if fuel_request.is_direct_deal:
            print(fuel_request.last_deal)
            search_company = FuelUpdate.objects.filter(id= fuel_request.last_deal).first()
            print(search_company.company_id)
            company = Company.objects.filter(id= search_company.company_id).first()
            print(company)

            fuel_request.request_company = company.name
        else:
            fuel_request.request_company = 'is not a direct deal'

    #print(type(fuel_requests))
    print(fuel_requests)
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
    if request.method == 'POST':
        form = FuelRequestForm(request.POST)
        if 'MakeDeal' in request.POST:
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
                fuel_request.is_direct_deal = True
                fuel_request.last_deal = request.POST.get('company_id')
                fuel_request.save()
            messages.success(request, f'kindly not your request has been made ')

        if 'WaitForOffer' in request.POST:
            if form.is_valid():
                amount = form.cleaned_data['amount']
                payment_method = form.cleaned_data['payment_method']
                delivery_method = form.cleaned_data['delivery_method']
                fuel_type = form.cleaned_data['fuel_type']
                fuel_request = FuelRequest()
                fuel_request.name = request.user       
                fuel_request.amount = amount
                fuel_request.fuel_type = fuel_type
                fuel_request.payment_method = payment_method
                fuel_request.delivery_method = delivery_method
                fuel_request.wait = True
                fuel_request.save()
            messages.success(request, f'kindly not your request has been made wait for an offer')

    else:
        form = FuelRequestForm
    
    updates = FuelUpdate.objects.filter(sub_type="depot")
    for update in updates:
        company = Company.objects.filter(id=update.company_id).first()
        if company is not None:
            update.company = company.name

    print(updates)
    return render(request, 'buyer/dashboard.html',{'form':form, 'updates': updates})



def offers(request, id):
    request = FuelRequest.objects.filter(id=id).first()
    offers = Offer.objects.filter(request=request).all()
    print(offers)
    return render(request, 'buyer/offer.html', {'offers': offers } )

