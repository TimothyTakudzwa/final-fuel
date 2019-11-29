from django.contrib.auth import authenticate, update_session_auth_hash, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.contrib import messages
import secrets

from datetime import date
from buyer.forms import BuyerUpdateForm
from company.models import Company, FuelUpdate
from .forms import PasswordChange, RegistrationForm, \
    RegistrationEmailForm, UserUpdateForm,  FuelRequestForm
from .models import  FuelRequest, Transaction, TokenAuthentication
from notification.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

# today's date
today = date.today()


def register(request):
    context = {
        'title': 'Fuel Finder | Register',
        'email': RegistrationEmailForm(),
        'registration': RegistrationForm()
    }
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if pass1 == pass2:
            User.objects.create_user(username=username, email=email, password=pass1)

            user = User.objects.get(username=username)
            user.is_active = False
            user.save()

            token = secrets.token_hex(12)
            TokenAuthentication.objects.create(token=token, user=user)
            domain = request.get_host()
            url = f'{domain}/verification/{token}/{user.id}'

            sender = f'Fuel Finder Accounts<tests@marlvinzw.me>'
            subject = 'User Registration'
            message = f"Dear {username} , complete signup here : \n {url} \n. Your password is {pass1}"

            try:
                msg = EmailMultiAlternatives(subject, message, sender, [f'{email}'])
                msg.send()

                messages.success(request, f"{username} Registered Successfully")
                return redirect('dashboard')

            except BadHeaderError:
                messages.warning(request, f"Oops , Something Wen't Wrong, Please Try Again")
                return redirect('register')
        else:
            messages.warning(request, "Passwords don't match")
            return redirect('register')
    return render(request, 'supplier/accounts/register.html', context=context)


def verification(request, token, user_id):
    context = {
        'title': 'Fuel Finder | Verification',
    }
    check = User.objects.filter(id=user_id)
    print("here l am ")

    if check.exists():
        user = User.objects.get(id=user_id)
        print(user)

        token_check = TokenAuthentication.objects.filter(user=user, token=token)
        result = bool([token_check])
        print(result)
        if result == True:
            if request.method == 'POST':
                user = User.objects.get(id=user_id)
                form = BuyerUpdateForm(request.POST, request.FILES, instance=user)
                if form.is_valid():
                    form.save()
                    company_id = request.POST.get('company_id')
                    print(f"---------Supplier {company_id} {type(company_id)}")
                    selected_company = Company.objects.filter(id=company_id).first()
                    user.company = selected_company
                    user.is_active = True
                    user.save()
                    return redirect('buyer-login')
            else:
                form = BuyerUpdateForm
                messages.success(request, f'Email verification successs, Fill in the deatails to complete registration')
                return render(request, 'supplier/accounts/verification.html', {'form': form})
        else:
            messages.warning(request, 'Wrong verification token')
            return redirect('login')
    else:
        messages.warning(request, 'Wrong verification id')
        return redirect('login')
    return render(request, 'supplier/accounts/verification.html', context=context)


def sign_in(request):
    context = {
        'title': 'Fuel Finder | Login',
    }
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        authenticated = authenticate(username=username, password=password)
        if authenticated:
            client = User.objects.get(username=username)
            login(request, client)
            
            messages.success(request, 'Welcome {client.username}')
            return redirect('dashboard')
        else:
            messages.warning(request, 'Incorrect username or password')
            return redirect('login')

    return render(request, 'supplier/accounts/login.html', context=context)


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
                return redirect('dashboard')
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
    if request.method == 'POST':
        userform = UserUpdateForm(request.POST, instance=request.user)
        if userform.is_valid():
            userform.save()
            messages.success(request, f'Profile successfully updated')
            return redirect('account')
        else:
            messages.warning(request, f'Something went wrong while saving your changes')
            return redirect('account')
    return render(request, 'supplier/accounts/account.html', context=context)


@login_required()
def fuel_request(request):
    context = {
        'title': 'Fuel Finder | Fuel Request',
        'requests': FuelRequest.objects.filter(date=today)
    }
    if request.method == 'POST':
        submitted_id = request.POST.get('request_id')
        if FuelRequest.objects.filter(id=submitted_id).exists():
            request_id = FuelRequest.objects.get(id=submitted_id)
            buyer_id = Profile.objects.get(id='')
            Transaction.objects.create(request_id=request_id,
                                       buyer_id=buyer_id)
            messages.success(request,
                             f'You have accepted a request for {request_id.amount} litres from {buyer_id.name}')
            return redirect('fuel-request')
    return render(request, 'supplier/accounts/fuel_request.html', context=context)


@login_required()
def rate_supplier(request):
    context = {
        'title': 'Fuel Finder | Rate Supplier',
    }
    return render(request, 'supplier/accounts/ratings.html', context=context)

@login_required
def fuel_update(request):
    if request.method == 'POST':
        if FuelUpdate.objects.filter(date=today, fuel_type=request.POST.get('fuel_type')).exists():
            closing_time = time.strftime("%H:%M:%S")
            max_amount = request.POST.get('max_amount')
            min_amount = request.POST.get('min_amount')
            deliver = request.POST.get('deliver')
            payment_method = request.POST.get('payment_method')
            fuel_type = request.POST.get('fuel_type')
            supplier_id = request.user.id
            FuelUpdate.objects.create(supplier_id=supplier_id, deliver=False, fuel_type=fuel_type, closing_time=closing_time, max_amount=max_amount, min_amount=min_amount, payment_method=payment_method)
            messages.success(request, 'Quantity uploaded successfully')
            return redirect('fuel-request')
        else:
            fuel_update = FuelUpdate.objects.get(fuel_type=request.POST.get('fuel_type'), date=today)
            fuel_update.max_amount = request.POST.get('max_amount')
            fuel_update.min_amount = request.POST.get('min_amount')
            fuel_update


    return render(request, 'supplier/accounts/ratings.html', context=context)


def offer(request, id):
    if request.method == "POST":
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        fuel_request = FuelRequest.objects.get(id=id)

        Offer.objects.create(price=price, quantity=quantity, supplier=request.user, request=fuel_request)
        
        messages.success(request, 'Offer uploaded successfully')
        action = f"{request.user}  made an offer of {quantity} @ {price}"

        AuditTrail.objects.create(user = request.user, action = action, reference = 'offer' )
        return redirect('fuel-request')
    else:
        messages.warning(request, 'Oops something went wrong while posting your offer')
    return render(request, 'supplier/accounts/fuel_request.html')


@login_required
def edit_offer(request, id):
    offer = Offer.objects.get(id=id)
    if request.method == 'POST':
        offer.price = request.POST.get('price')
        offer.quantity = request.POST.get('quantity')
        offer.save()
        messages.success(request, 'Offer successfully updated')
        return redirect('fuel-request')
    return render(request, 'supplier/accounts/fuel-request.html')

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