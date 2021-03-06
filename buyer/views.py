import secrets
from datetime import datetime
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.shortcuts import redirect, render
from django.http import HttpResponse
from buyer.models import User
from buyer.recommend import recommend
from company.models import Company, FuelUpdate
from supplier.models import Offer, Subsidiaries, Transaction, TokenAuthentication, UserReview

from .constants import sample_data
from .forms import BuyerRegisterForm, PasswordChange, FuelRequestForm, PasswordChangeForm, LoginForm
from .models import FuelRequest
from buyer.utils import render_to_pdf
from notification.models import Notification

user = get_user_model()


# The login in functions, it handles how users are authenticated into the system
# Users are redirected to their landing page based on whether they are in which group


def login_user(request):
    context = {
        'form': LoginForm()
    }
    # check if a user's session exists
    if request.user.is_authenticated:
        current_user = User.objects.get(username=request.user.username)
        # redirecting to the set pages
        if current_user.user_type == "BUYER":
            return redirect("buyer-dashboard")
        elif current_user.user_type == 'SS_SUPPLIER':
            return redirect("serviceStation:home")
        elif current_user.user_type == 'SUPPLIER':
            return redirect("fuel-request")
        elif current_user.user_type == 'S_ADMIN':
            return redirect("users:allocate")
    else:
        # signing in
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            # checking if a user exists
            user_check = User.objects.filter(username=username).exists()
            if user_check:
                # user exists
                auth_user = User.objects.get(username=username)
                # checking if user has completed registration
                if auth_user.is_active:
                    auth_status = authenticate(username=username, password=password)
                    # user has entered details correctly
                    if auth_status:
                        current_user = User.objects.get(username=username)
                        # starting session
                        login(request, current_user)
                        # redirecting to the necessary pages
                        if current_user.user_type == "BUYER":
                            return redirect("buyer-dashboard")
                        elif current_user.user_type == 'SS_SUPPLIER':
                            return redirect("serviceStation:home")
                        elif current_user.user_type == 'SUPPLIER':
                            return redirect("fuel-request")
                        elif current_user.user_type == 'S_ADMIN':
                            return redirect("users:allocate")
                        else:
                            return redirect("users:suppliers_list")
                    # wrong password
                    else:
                        messages.info(request, 'Wrong password')
                        return redirect('login')
                # user hasn't completed registration yet
                else:
                    messages.info(request, 'Your account is waiting for approval. Please check your email '
                                           'or contact your company administrator')
                    return redirect('login')
            # throw account not found error
            else:
                messages.info(request, 'Please register first')
                return redirect('login')
    return render(request, 'buyer/signin.html', context=context)


# The function is responsible for sending emails after successful completions of stage one registration
# The function generates the authentication token
# The second registration is in supplier view "Verification", responsible for authentication token verification

def token_is_send(request, user):
    token = secrets.token_hex(12)
    token_id = user
    token_auth = TokenAuthentication()
    token_auth.token = token
    token_auth.user = token_id
    token_auth.save()
    domain = request.get_host()
    url = f'https://{domain}/verification/{token}/{user.id}'
    print(url)
    sender = "intelliwhatsappbanking@gmail.com"
    subject = 'Fuel Finder Registration'
    message = f"Dear {user.first_name}  {user.last_name}. \nYour username is: {user.username}\n\nPlease complete signup here : \n {url} \n. "
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


# Stage one registration view

def register(request):
    if request.method == 'POST':
        form = BuyerRegisterForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            user_type = form.cleaned_data['user_type']
            full_name = first_name + " " + last_name
            i = 0
            username = initial_username = first_name[0] + last_name
            while User.objects.filter(username=username.lower()).exists():
                username = initial_username + str(i)
                i += 1
            user = User.objects.create(email=email, username=username.lower(), user_type=user_type,
                                       phone_number=phone_number.replace(" ", ""), first_name=first_name,
                                       last_name=last_name, is_active=False)
            if token_is_send(request, user):
                if user.is_active:
                    messages.success(user.phone_number, "You have been registered succesfully")
                    user.stage = 'requesting'
                    user.save()

                return render(request, 'buyer/email_send.html')
            else:
                # messages.warning(request, f"Oops , Something Wen't Wrong, Please Try Again")
                return render(request, 'buyer/email_send.html')

        else:
            msg = "Error!!! We have a user with this user email-id"
            messages.error(request, msg)
            return redirect('buyer-register')
    else:
        form = BuyerRegisterForm

    return render(request, 'buyer/signup.html', {'form': form})


# function repsonsible for sending token to whatsapp
def send_message(phone_number, message):
    payload = {
        "phone": phone_number,
        "body": message
    }
    url = "https://eu33.chat-api.com/instance78632/sendMessage?token=sq0pk8hw4iclh42b"
    r = requests.post(url=url, data=payload)
    print(r)
    return r.status_code


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
                return redirect('bchange-password')
            elif new1 == old:
                messages.warning(request, "New password can not be similar to the old one")
                return redirect('bchange-password')
            elif len(new1) < 8:
                messages.warning(request, "Password is too short")
                return redirect('bchange-password')
            elif new1.isnumeric():
                messages.warning(request, "Password can not be entirely numeric!")
            elif not new1.isalnum():
                messages.warning(request, "Password should be alphanumeric")
                return redirect('bchange-password')
            else:
                user = request.user
                user.set_password(new1)
                user.save()
                update_session_auth_hash(request, user)

                messages.success(request, 'Password Successfully Changed')
                return redirect('buyer-profile')
        else:
            messages.warning(request, 'Wrong Old Password, Please Try Again')
            return redirect('bchange-password')
    return render(request, 'buyer/change_password.html', context=context)


@login_required()
# for loading user profile, editing profile and changing password
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


# The function based view is responsible for showing the buyer request.
# The requests shown are those that are not complete and             that have been made buy the buyer.

@login_required()
def fuel_request(request):
    user_logged = request.user
    fuel_requests = FuelRequest.objects.filter(name=user_logged, is_complete=False).all()
    for fuel_request in fuel_requests:
        if fuel_request.is_direct_deal:
            search_company = FuelUpdate.objects.filter(relationship_id=fuel_request.last_deal).first()
            depot = Subsidiaries.objects.filter(id=search_company.relationship_id).first()
            company = Company.objects.filter(id=search_company.company_id).first()
            fuel_request.request_company = company.name
            fuel_request.depot = depot.name
        else:
            fuel_request.request_company = ''
    for fuel_request in fuel_requests:
        offer = Offer.objects.filter(request=fuel_request).filter(declined=False).first()
        if offer is not None:
            fuel_request.has_offers = True
        else:
            fuel_request.has_offers = False

    context = {
        'fuel_requests': fuel_requests
    }

    return render(request, 'buyer/fuel_request.html', context=context)


def fuel_finder(request):
    if request.method == 'POST':
        form = FuelRequestForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            delivery_method = form.cleaned_data['delivery_method']
            fuel_type = form.cleaned_data['fuel_type']
            print(f"===================={request.POST.get('company_id')}--------------------  ")
            fuel_request = FuelRequest()
            fuel_request.name = request.user
            fuel_request.amount = amount
            fuel_request.fuel_type = fuel_type
            # fuel_request.payment_method = payment_method
            fuel_request.delivery_method = delivery_method
            fuel_request.wait = True
            fuel_request.save()
            messages.success(request, f'kindly note your request has been made ')

            message = f'{request.user.company.name.title()} made a request of {fuel_request.amount}L {fuel_request.fuel_type.lower()}'
            Notification.objects.create(message=message, reference_id=fuel_request.id, action="new_request")
    else:
        form = FuelRequestForm
    return render(request, 'buyer/dashboard.html', {'form': form, 'sample_data': sample_data})


def dashboard(request):
    updates = FuelUpdate.objects.filter(sub_type="Suballocation").filter(~Q(diesel_quantity=0.00)).filter(
        ~Q(petrol_quantity=0.00))
    for update in updates:
        subsidiary = Subsidiaries.objects.filter(id=update.relationship_id).first()
        if UserReview.objects.filter(depot=subsidiary).exists():
            ratings = UserReview.objects.filter(depot=subsidiary).all()
            sum_rate = 0
            rate_count = 0
            for rate in ratings:
                sum_rate = sum_rate + rate.rating
                rate_count += 1
            update.rating = round(sum_rate / rate_count)
        else:
            update.rating = '-'

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
                fuel_request.payment_method = request.POST.get('fuel_payment_method')
                fuel_request.delivery_method = form.cleaned_data['delivery_method']
                fuel_request.delivery_address = request.POST.get('s_number') + " " + request.POST.get(
                    's_name') + " " + request.POST.get('s_town')
                fuel_request.storage_tanks = request.POST.get('storage_tanks')
                fuel_request.pump_required = True if request.POST.get('pump_required') == "on" else False
                fuel_request.dipping_stick_required = True if request.POST.get(
                    'dipping_stick_required') == "on" else False
                fuel_request.meter_required = True if request.POST.get('meter_required') == "on" else False
                fuel_request.is_direct_deal = True
                fuel_request.last_deal = request.POST.get('company_id')
                print(fuel_request.meter_required)
                fuel_request.save()
                user = User.objects.filter(subsidiary_id=fuel_request.last_deal).first()
            messages.success(request, f'kindly note your request has been made ')
            message = f'{request.user.first_name} {request.user.last_name} made a request of {fuel_request.amount}L {fuel_request.fuel_type.lower()}'
            Notification.objects.create(message=message, user=user, reference_id=fuel_request.id, action="new_request",
                                        user_id=request.user.id)

        if 'WaitForOffer' in request.POST:
            if form.is_valid():
                fuel_request = FuelRequest()
                fuel_request.name = request.user
                fuel_request.amount = form.cleaned_data['amount']
                fuel_request.fuel_type = form.cleaned_data['fuel_type']
                fuel_request.payment_method = request.POST.get('fuel_payment_method')
                fuel_request.delivery_method = form.cleaned_data['delivery_method']
                fuel_request.delivery_address = request.POST.get('s_number') + " " + request.POST.get(
                    's_name') + " " + request.POST.get('s_town')
                fuel_request.storage_tanks = request.POST.get('storage_tanks')
                fuel_request.pump_required = True if request.POST.get('pump_required') == "True" else False
                fuel_request.dipping_stick_required = True if request.POST.get('dipping_stick_required') == "True" else False
                fuel_request.meter_required = True if request.POST.get('meter_required') == "True" else False
                fuel_request.wait = True
                fuel_request.save()
            messages.success(request, f'Fuel Request has been submitted succesfully and now waiting for an offer')
            message = f'{request.user.first_name} {request.user.last_name} made a request of {fuel_request.amount}L {fuel_request.fuel_type.lower()}'
            Notification.objects.create(message=message, user=request.user, reference_id=fuel_request.id,
                                        action="new_request")

        if 'Recommender' in request.POST:
            if form.is_valid():
                amount = form.cleaned_data['amount']
                delivery_method = form.cleaned_data['delivery_method']
                fuel_type = form.cleaned_data['fuel_type']
                fuel_request = FuelRequest()
                fuel_request.name = request.user
                fuel_request.payment_method = request.POST.get('fuel_payment_method')
                print(fuel_request.payment_method)
                fuel_request.amount = amount
                fuel_request.fuel_type = fuel_type
                fuel_request.delivery_method = delivery_method
                fuel_request.save()
                offer_id, response_message = recommend(fuel_request)
                if not offer_id:
                    messages.error(request, response_message)
                else:
                    offer = Offer.objects.filter(id=offer_id).first()
                    messages.info(request, "Match Found")
                    return render(request, 'buyer/dashboard.html', {'form': form, 'updates': updates, 'offer': offer})
    else:
        form = FuelRequestForm
    return render(request, 'buyer/dashboard.html', {'form': form, 'updates': updates})


def offers(request, id):
    selected_request = FuelRequest.objects.filter(id=id).first()
    offers = Offer.objects.filter(request=selected_request).filter(declined=False).all()
    buyer = request.user
    for offer in offers:
        depot = Subsidiaries.objects.filter(id=offer.supplier.subsidiary_id).first()
        if depot:
            offer.depot_name = depot.name

    return render(request, 'buyer/offer.html', {'offers': offers})


def new_offer(request, id):
    offers = Offer.objects.filter(id=id).all()
    return render(request, 'buyer/new_offer.html', {'offers': offers})


def new_fuel_offer(request, id):
    offers = Offer.objects.filter(id=id).all()
    return render(request, 'buyer/new_offer.html', {'offers': offers})


def accept_offer(request, id):
    offer = Offer.objects.filter(id=id).first()
    Transaction.objects.create(offer=offer, buyer=request.user, supplier=offer.supplier, is_complete=False)
    FuelRequest.objects.filter(id=offer.request.id).update(is_complete=True)
    offer.is_accepted = True
    offer.save()

    message = f'{offer.request.name.first_name} {offer.request.name.last_name} accepted your offer of {offer.quantity}L {offer.request.fuel_type.lower()} at ${offer.price}'
    Notification.objects.create(message=message, user=offer.supplier, reference_id=offer.id, action="ofer_accepted")

    messages.warning(request, "Your request has been saved successfully")
    return redirect("buyer-transactions")


def reject_offer(request, id):
    offer = Offer.objects.filter(id=id).first()
    offer.declined = True
    offer.save()
    my_request = FuelRequest.objects.filter(id=offer.request.id).first()
    my_request.wait = True
    my_request.is_complete = False
    my_request.save()

    message = f'{offer.request.name.first_name} {offer.request.name.last_name} rejected your offer of {offer.quantity}L {offer.request.fuel_type.lower()} at ${offer.price}'
    Notification.objects.create(message=message, user=offer.supplier, reference_id=offer.id, action="offer_rejected")

    # FuelRequest.objects.filter(id=offer.request.id).update(is_complete=True)
    messages.success(request,
                     "Your request has been saved and as offer updates are coming you will receive notifications")
    return redirect("buyer-fuel-request")


def transactions(request):
    if request.method == "POST":
        # print(f"________{Transaction.objects.get(id=request.POST.get('transaction_id'))}__________")
        # print(f"_____________{request.POST.get('rating')}______________")
        # print(f"_____________{request.POST.get('comment')}______________")
        tran = Transaction.objects.get(id=request.POST.get('transaction_id'))
        now = datetime.now(),
        from supplier.models import UserReview
        UserReview.objects.create(
            rater=request.user,
            rating=int(request.POST.get('rating')),
            company=tran.supplier.company,
            transaction=tran,
            depot=Subsidiaries.objects.filter(id=tran.supplier.subsidiary_id).first(),
            comment=request.POST.get('comment')
        )
        messages.success(request, 'Transaction Successfully Reviewed')

    buyer = request.user
    transactions = Transaction.objects.filter(buyer=buyer).all()
    for transaction in transactions:
        subsidiary = Subsidiaries.objects.filter(id=transaction.supplier.subsidiary_id).first()
        if subsidiary is not None:
            transaction.depot = subsidiary.name
            transaction.address = subsidiary.address
        from supplier.models import UserReview
        transaction.review = UserReview.objects.filter(transaction=transaction).first()

    context = {
        'transactions': transactions
    }

    return render(request, 'buyer/transactions.html', context=context)


def transactions_review_delete(request, id):
    from supplier.models import UserReview
    rev = UserReview.objects.filter(id=id).first()
    rev.delete()
    messages.success(request, 'Review Successfully Deleted')
    return redirect("buyer-transactions")


def transaction_review_edit(request, id):
    from supplier.models import UserReview
    review = UserReview.objects.filter(id=id).first()
    if request.method == "POST":
        review.rating = int(request.POST.get('rating'))
        review.comment = request.POST.get('comment')
        review.save()
        messages.success(request, 'Review Successfully Edited')
    return redirect("buyer-transactions")


def invoice(request, id):
    buyer = request.user
    transactions = Transaction.objects.filter(buyer=buyer, id=id).first()

    context = {
        'transactions': transactions
    }
    pdf = render_to_pdf('buyer/invoice.html', context)
    return HttpResponse(pdf, content_type='application/pdf')


def view_invoice(request, id):
    buyer = request.user
    transaction = Transaction.objects.filter(buyer=buyer, id=id).all()
    for transaction in transaction:
        subsidiary = Subsidiaries.objects.filter(id=transaction.supplier.subsidiary_id).first()
        if subsidiary is not None:
            transaction.depot = subsidiary.name
            transaction.address = subsidiary.address
            print('l am here')
            print(transaction.depot)

    total = transaction.offer.quantity * transaction.offer.price
    print(total)
    g_total = total + 25

    context = {
        'transaction': transaction,
        'total': total,
        'g_total': g_total
    }
    return render(request, 'buyer/invoice2.html', context)
