import secrets
from datetime import date

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from weasyprint import HTML

from accounts.models import Account
from buyer.models import User
from accounts.models import AccountHistory
from buyer.recommend import recommend
from buyer.utils import render_to_pdf
from company.models import Company
from notification.models import Notification
from supplier.forms import DeliveryScheduleForm
from supplier.lib import total_requests, transactions_total_cost, total_offers
from supplier.models import Offer, Subsidiaries, DeliverySchedule, Transaction, TokenAuthentication, \
    UserReview, SuballocationFuelUpdate
from .constants import sample_data
from .forms import BuyerRegisterForm, PasswordChange, FuelRequestForm, PasswordChangeForm, LoginForm
from .models import FuelRequest

user = get_user_model()

"""

The login in functions, it handles how users are authenticated into the system
Users are redirected to their landing page based on whether they are in which group


"""


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


"""

The function is responsible for sending emails after successful completions of stage one registration
The function generates the authentication token
The second registration is in supplier view "Verification", responsible for authentication token verification

"""


def token_is_send(request, auth_user):
    token = secrets.token_hex(12)
    token_id = auth_user
    token_auth = TokenAuthentication()
    token_auth.token = token
    token_auth.user = token_id
    token_auth.save()
    domain = request.get_host()
    url = f'https://{domain}/verification/{token}/{auth_user.id}'
    sender = "intelliwhatsappbanking@gmail.com"
    subject = 'Fuel Finder Registration'
    message = f"Dear {auth_user.first_name}  {auth_user.last_name}. \nYour username is: " \
              f"{auth_user.username}\n\nPlease complete " \
              f"signup here : \n {url} \n. "
    # noinspection PyBroadException
    try:
        msg = EmailMultiAlternatives(subject, message, sender, [f'{auth_user.email}'])
        msg.send()
        messages.success(request, f"{auth_user.first_name}  {auth_user.last_name} Registered Successfully")
        return True
    except Exception:
        messages.warning(request, f"Oops , Something Wen't Wrong, Please Try Again")
        return False
        messages.success(request, ('Your profile was successfully updated!'))
    return render(request, 'buyer/send_email.html')


"""

Stage one registration view

"""


def register(request):
    if request.method == 'POST':
        form = BuyerRegisterForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            user_type = form.cleaned_data['user_type']
            i = 0
            username = initial_username = first_name[0] + last_name
            while User.objects.filter(username=username.lower()).exists():
                username = initial_username + str(i)
                i += 1
            auth_user = User.objects.create(email=email, username=username.lower(), user_type=user_type,
                                            phone_number=phone_number.replace(" ", ""), first_name=first_name,
                                            last_name=last_name, is_active=False)
            if token_is_send(request, auth_user):
                if auth_user.is_active:
                    messages.success(auth_user.phone_number, "You have been registered succesfully")
                    auth_user.stage = 'requesting'
                    auth_user.save()

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


"""

function responsible for sending token to whatsapp

"""


def send_message(phone_number, message):
    payload = {
        "phone": phone_number,
        "body": message
    }
    url = "https://eu33.chat-api.com/instance78632/sendMessage?token=sq0pk8hw4iclh42b"
    r = requests.post(url=url, data=payload)
    return r.status_code


"""

Change password 

"""


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
                current_user = request.user
                current_user.set_password(new1)
                current_user.save()
                update_session_auth_hash(request, current_user)

                messages.success(request, 'Password Successfully Changed')
                return redirect('buyer-profile')
        else:
            messages.warning(request, 'Wrong Old Password, Please Try Again')
            return redirect('bchange-password')
    return render(request, 'buyer/change_password.html', context=context)


"""

for loading user profile, editing profile and changing password

"""


@login_required()
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
                current_user = request.user
                current_user.set_password(new1)
                current_user.save()
                update_session_auth_hash(request, current_user)

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


"""

The function based view is responsible for showing the buyer request.
The requests shown are those that are not complete and             that have been made buy the buyer.

"""


@login_required()
def fuel_request(request):
    user_logged = request.user
    fuel_requests = FuelRequest.objects.filter(name=user_logged, is_complete=False).all()
    for fuel_request_item in fuel_requests:
        if fuel_request_item.is_direct_deal:
            depot = Subsidiaries.objects.filter(id=fuel_request_item.last_deal).first()
            if depot is not None:
                company = Company.objects.filter(id=depot.company.id).first()
                fuel_request_item.request_company = company.name
                fuel_request_item.depot = depot.name
            else:
                pass
        else:
            fuel_request_item.request_company = ''
    for fuel_request_item in fuel_requests:
        offer = Offer.objects.filter(request=fuel_request_item).filter(declined=False).first()
        if offer is not None:
            fuel_request_item.has_offers = True
        else:
            fuel_request_item.has_offers = False

    context = {
        'fuel_requests': fuel_requests
    }

    return render(request, 'buyer/fuel_request.html', context=context)


"""

Looking for fuel from suppliers

"""


@login_required
def fuel_finder(request):
    if request.method == 'POST':
        form = FuelRequestForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            delivery_method = form.cleaned_data['delivery_method']
            fuel_type = form.cleaned_data['fuel_type']
            fuel_request_item = FuelRequest()
            fuel_request_item.name = request.user
            fuel_request_item.amount = amount
            fuel_request_item.fuel_type = fuel_type
            fuel_request_item.delivery_method = delivery_method
            fuel_request_item.wait = True
            fuel_request_item.save()
            messages.success(request, f'kindly note your request has been made ')

            message = f'{request.user.company.name.title()} made a request of {fuel_request_item.amount}L' \
                      f' {fuel_request_item.fuel_type.lower()}'
            Notification.objects.create(message=message, reference_id=fuel_request_item.id, action="new_request")
    else:
        form = FuelRequestForm
    return render(request, 'buyer/dashboard.html', {'form': form, 'sample_data': sample_data})


"""

Landing page

"""


@login_required
def dashboard(request):
    if request.user.company.is_govnt_org:
        updates = SuballocationFuelUpdate.objects.filter(~Q(subsidiary__praz_reg_num=None)).filter(
            ~Q(diesel_quantity=0.00)).filter(~Q(petrol_quantity=0.00))
    else:
        updates = SuballocationFuelUpdate.objects.filter(~Q(diesel_quantity=0.00)).filter(~Q(petrol_quantity=0.00))
    for update in updates:
        subsidiary = Subsidiaries.objects.filter(id=update.subsidiary.id).first()
        if UserReview.objects.filter(depot=subsidiary).exists():
            ratings = UserReview.objects.filter(depot=subsidiary).all()
            sum_rate = 0
            rate_count = 0
            for rate in ratings:
                sum_rate = sum_rate + rate.rating
                rate_count += 1
            update.rating = round(sum_rate / rate_count)
        else:
            update.rating = 0

        sub = Subsidiaries.objects.filter(id=update.subsidiary.id).first()
        company = Company.objects.filter(id=sub.company.id).first()
        if company is not None:
            update.company = company.name
            update.depot = subsidiary.name
            update.address = subsidiary.address
    if request.method == 'POST':
        form = FuelRequestForm(request.POST)
        if 'MakeDeal' in request.POST:
            if form.is_valid():
                fuel_request_object = FuelRequest()
                fuel_request_object.name = request.user
                fuel_request_object.amount = int(form.cleaned_data['amount'])
                fuel_request_object.fuel_type = form.cleaned_data['fuel_type']
                fuel_request_object.payment_method = request.POST.get('fuel_payment_method')
                fuel_request_object.delivery_method = form.cleaned_data['delivery_method']
                fuel_request_object.delivery_address = request.POST.get('s_number') + " " + request.POST.get(
                    's_name') + " " + request.POST.get('s_town')
                fuel_request_object.storage_tanks = request.POST.get('storage_tanks')
                fuel_request_object.pump_required = True if request.POST.get('pump_required') == "on" else False
                fuel_request_object.dipping_stick_required = True if request.POST.get(
                    'dipping_stick_required') == "on" else False
                fuel_request_object.meter_required = True if request.POST.get('meter_required') == "on" else False
                fuel_request_object.is_direct_deal = True
                fuel_request_object.last_deal = int(request.POST.get('company_id'))
                fuel_request_object.save()
                current_user = User.objects.filter(subsidiary_id=fuel_request_object.last_deal).first()
            messages.success(request, f'kindly note your request has been made ')
            message = f'{request.user.first_name} {request.user.last_name} made a request of ' \
                      f'{fuel_request_object.amount}L {fuel_request_object.fuel_type.lower()}'
            Notification.objects.create(message=message, user=current_user, reference_id=fuel_request_object.id,
                                        action="new_request", user_id=request.user.id)
            return redirect('buyer-dashboard')

        if 'WaitForOffer' in request.POST:
            if form.is_valid():
                fuel_request_object = FuelRequest()
                fuel_request_object.name = request.user
                fuel_request_object.amount = form.cleaned_data['amount']
                fuel_request_object.fuel_type = form.cleaned_data['fuel_type']
                fuel_request_object.payment_method = request.POST.get('fuel_payment_method')
                fuel_request_object.delivery_method = form.cleaned_data['delivery_method']
                fuel_request_object.delivery_address = request.POST.get('s_number') + " " + request.POST.get(
                    's_name') + " " + request.POST.get('s_town')
                fuel_request_object.storage_tanks = request.POST.get('storage_tanks')
                fuel_request_object.pump_required = True if request.POST.get('pump_required') == "True" else False
                fuel_request_object.dipping_stick_required = True if request.POST.get(
                    'dipping_stick_required') == "True" else False
                fuel_request_object.meter_required = True if request.POST.get('meter_required') == "True" else False
                fuel_request_object.wait = True
                fuel_request_object.save()
            messages.success(request, f'Fuel Request has been submitted successfully and now waiting for an offer')
            message = f'{request.user.first_name} {request.user.last_name} made a request of ' \
                      f'{fuel_request_object.amount}L {fuel_request_object.fuel_type.lower()}'
            Notification.objects.create(message=message, user=request.user, reference_id=fuel_request_object.id,
                                        action="new_request")
            return redirect('buyer-dashboard')

        if 'Recommender' in request.POST:
            if form.is_valid():
                amount = form.cleaned_data['amount']
                delivery_method = form.cleaned_data['delivery_method']
                fuel_type = form.cleaned_data['fuel_type']
                fuel_request_object = FuelRequest()
                fuel_request_object.name = request.user
                fuel_request_object.payment_method = request.POST.get('fuel_payment_method')
                fuel_request_object.amount = amount
                fuel_request_object.fuel_type = fuel_type
                fuel_request_object.delivery_method = delivery_method
                fuel_request_object.save()
                offer_id, response_message = recommend(fuel_request_object)
                if not offer_id:
                    messages.error(request, response_message)
                else:
                    offer = Offer.objects.filter(id=offer_id).first()
                    sub = Subsidiaries.objects.filter(id=offer.supplier.subsidiary_id).first()
                    messages.info(request, "Match Found")
                    return render(request, 'buyer/dashboard.html',
                                  {'form': form, 'updates': updates, 'offer': offer, 'sub': sub})
    else:
        form = FuelRequestForm
    return render(request, 'buyer/dashboard.html', {'form': form, 'updates': updates})


"""

Offers


"""


@login_required
def offers(request, id):
    selected_request = FuelRequest.objects.filter(id=id).first()
    offers = Offer.objects.filter(request=selected_request).filter(declined=False).all()
    for offer in offers:
        depot = Subsidiaries.objects.filter(id=offer.supplier.subsidiary_id).first()
        if depot:
            offer.depot_name = depot.name

    return render(request, 'buyer/offer.html', {'offers': offers})


"""

Offer Handlers

"""


@login_required
def new_offer(request, user_id):
    offers_available = Offer.objects.filter(id=user_id).all()
    return render(request, 'buyer/new_offer.html', {'offers': offers_available})


@login_required
def new_fuel_offer(request, user_id):
    offers_present = Offer.objects.filter(id=user_id).all()
    return render(request, 'buyer/new_offer.html', {'offers': offers_present})


@login_required
def accept_offer(request, id):
    offer = Offer.objects.filter(id=id).first()
    expected = int(offer.quantity * offer.price) + int(offer.transport_fee)
    Transaction.objects.create(offer=offer, buyer=request.user, supplier=offer.supplier, is_complete=False,expected = expected)
    FuelRequest.objects.filter(id=offer.request.id).update(is_complete=True)
    offer.is_accepted = True
    offer.save()

    message = f'{offer.request.name.first_name} {offer.request.name.last_name} accepted your offer of {offer.quantity}L {offer.request.fuel_type.lower()} at ${offer.price}'
    Notification.objects.create(message=message, user=offer.supplier, reference_id=offer.id, action="offer_accepted")

    messages.warning(request, "Your request has been saved successfully")
    return redirect("buyer-transactions")


@login_required
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


"""

Transaction Handlers

"""


@login_required
def transactions(request):
    if request.method == "POST":
        if request.POST.get('buyer_company_id') is not None:
            buyer_transactions = AccountHistory.objects.filter(
                transaction__buyer__company__id=int(request.POST.get('buyer_company_id')),
                transaction__supplier__company__id=int(request.POST.get('supplier_company_id')),
            )
            html_string = render_to_string('supplier/export.html', {'transactions': buyer_transactions,
                          'supplier_details': AccountHistory.objects.filter(
                              transaction__supplier_id=request.POST.get('supplier_company_id')),
                          'buyer_details': AccountHistory.objects.filter(transaction__buyer_id=int(
                              request.POST.get('buyer_company_id')))
                            })
            html = HTML(string=html_string)
            export_name = f"{request.POST.get('buyer_name')}{date.today().strftime('%H%M%S')}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = 'attachment;filename=export.pdf'
                return response
        else:
            tran = Transaction.objects.get(id=request.POST.get('transaction_id'))
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
            return redirect('buyer-transactions')

    buyer = request.user
    all_transactions = Transaction.objects.filter(buyer=buyer).all()
    for transaction in all_transactions:
        subsidiary = Subsidiaries.objects.filter(id=transaction.supplier.subsidiary_id).first()
        delivery_schedules = DeliverySchedule.objects.filter(transaction__id=transaction.id).exists()
        if delivery_schedules:
            transaction.delivery_schedule = True
            transaction.delivery_object = DeliverySchedule.objects.filter(transaction__id=transaction.id).first()
        else:
            transaction.delivery_schedule = False
            transaction.delivery_object = None
        if subsidiary is not None:
            transaction.depot = subsidiary.name
            transaction.address = subsidiary.location
        from supplier.models import UserReview
        transaction.review = UserReview.objects.filter(transaction=transaction).first()

    context = {
        'transactions': all_transactions,
        'subsidiary': Subsidiaries.objects.filter(),
        'all_transactions': AccountHistory.objects.filter()
    }

    return render(request, 'buyer/transactions.html', context=context)


@login_required
def transactions_review_delete(request, transaction_id):
    from supplier.models import UserReview
    rev = UserReview.objects.filter(id=transaction_id).first()
    rev.delete()
    messages.success(request, 'Review Successfully Deleted')
    return redirect("buyer-transactions")


@login_required
def transaction_review_edit(request, user_id):
    from supplier.models import UserReview
    review = UserReview.objects.filter(id=user_id).first()
    if request.method == "POST":
        review.rating = int(request.POST.get('rating'))
        review.comment = request.POST.get('comment')
        review.save()
        messages.success(request, 'Review Successfully Edited')
    return redirect("buyer-transactions")


"""

Invoice Handlers
 
"""


@login_required
def invoice(request, user_id):
    buyer = request.user
    transactions_availabe = Transaction.objects.filter(buyer=buyer, id=user_id).first()

    context = {
        'transactions': transactions_availabe
    }

    pdf = render_to_pdf('buyer/invoice.html', context)
    return HttpResponse(pdf, content_type='application/pdf')


@login_required
def view_invoice(request, user_id):
    buyer = request.user
    transaction = Transaction.objects.filter(buyer=buyer, id=user_id).all()
    for transaction in transaction:
        subsidiary = Subsidiaries.objects.filter(id=transaction.supplier.subsidiary_id).first()
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
    return render(request, 'buyer/invoice2.html', context)


@login_required
def delivery_schedules(request):
    schedules = DeliverySchedule.objects.filter(transaction__buyer=request.user)
    for schedule in schedules:
        schedule.subsidiary = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
        if schedule.transaction.offer.delivery_method.lower() == 'delivery':
            if schedule.transaction.offer.request.delivery_address.strip() == "":
                depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                schedule.delivery_address = depot.location
            else:
                if schedule.transaction.offer.request.delivery_address != None:
                    schedule.delivery_address = schedule.transaction.offer.request.delivery_address
                else:
                    depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                    schedule.delivery_address = depot.location
        else:
            if schedule.transaction.offer.collection_address.strip()=="":
                depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                schedule.delivery_address = depot.location
            else:
                if schedule.transaction.offer.collection_address != None:
                    schedule.delivery_address = schedule.transaction.offer.collection_address 
                else:
                    depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                    schedule.delivery_address = depot.location
    context = {'form': DeliveryScheduleForm(),
               'schedules': schedules
               }
    if request.method == 'POST':
        confirmation_document = request.FILES.get('confirmation_document')
        delivery_id = request.POST.get('delivery_id')

        schedule = DeliverySchedule.objects.get(id=delivery_id)
        schedule.confirmation_document = confirmation_document
        schedule.save()
        messages.success(request, 'Delivery successfully confirmed!!!')
        message = f"Delivery Confirmed for {schedule.transaction.buyer.company}, Click To View Confirmation Document"
        Notification.objects.create(user=request.user, action='DELIVERY', message=message, reference_id=schedule.id)
        return redirect('delivery-schedule')

    return render(request, 'buyer/delivery_schedules.html', context=context)


def delivery_schedule(request, id):
    schedule = DeliverySchedule.objects.filter(id=id).first()
    schedule.subsidiary = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
    if schedule.transaction.offer.delivery_method.lower() == 'delivery':
        schedule.delivery_address = schedule.transaction.offer.request.delivery_address
    else:
        schedule.delivery_address = schedule.transaction.offer.collection_address
    context = {
        'form': DeliveryScheduleForm(),
        'schedule': schedule
    }
    return render(request, 'buyer/delivery_schedule.html', context=context)


"""

Buyer Accounts

"""


def accounts(request):
    accounts_available = Account.objects.filter(buyer_company=request.user.company).all()
    fuel_orders = FuelRequest.objects.filter(private_mode=True).all().order_by('date')
    order_nums, latest_orders = total_requests(request.user.company)
    total_costs = transactions_total_cost(request.user)
    offers_count_all, offers_count_today = total_offers(request.user)
    return render(request, 'buyer/accounts.html',
                  {'accounts': accounts_available, 'fuel_orders': fuel_orders, 'order_nums': order_nums,
                   'latest_orders': latest_orders, 'total_costs': total_costs, 'offers_count_all': offers_count_all,
                   'offers_count_today': offers_count_today})


"""

Direct Request

"""


def make_direct_request(request):
    """
    Function To Make Direct Requests With A Particular Supplier
    """
    if request.method == "POST":
        supplier = User.objects.filter(company__id=int(request.POST.get('supplier_id'))).first()
        if supplier:
            fuel_request_object = FuelRequest.objects.create(
                name=request.user,
                is_direct_deal=True,
                fuel_type=request.POST.get('fuel_type'),
                amount=request.POST.get('quantity'),
                payment_method=request.POST.get('currency'),
                delivery_method=request.POST.get('delivery_method'),
                supplier_company=supplier.company,
                wait=True,
                private_mode=True,
            )
            messages.success(request, f"Successfully Made An Order to {supplier.company.name}")
            message = f'{request.user.company.name.title()} made a request of ' \
                      f'{fuel_request_object.amount}L {fuel_request_object.fuel_type.lower()}'
            Notification.objects.create(user=supplier, message=message, reference_id=fuel_request_object.id,
                                        action="new_request")
        else:
            messages.warning(request, f"Supplier Not Found")

    return redirect('buyer:accounts')


"""

Edit Account Details

"""


def edit_account_details(request, user_id):
    account = Account.objects.filter(id=user_id).first()
    if request.method == "POST":
        account.account_number = request.POST.get('account_number')
        account.save()
        messages.success(request, f"Successfully Made Changes To Account Details")
    return redirect('buyer:accounts')


"""

Make private request

"""


def make_private_request(request):
    """
    This Function Will Retrieve Form Data and Create A Request With Only The Suppliers
    That The Buyer Has An Account With
    """
    if request.method == "POST":
        # supplier = User.objects.filter(company__id=account.supplier_company.id).first()
        fuel_request_object = FuelRequest.objects.create(
            name=request.user,
            is_direct_deal=False,
            fuel_type=request.POST.get('fuel_type'),
            amount=request.POST.get('quantity'),
            payment_method=request.POST.get('currency'),
            delivery_method=request.POST.get('delivery_method'),
            # supplier=account.supplier_company,
            private_mode=True,
            wait=True,
        )
        message = f'{request.user.company.name.title()} made a private request of' \
                  f' {fuel_request_object.amount}L {fuel_request_object.fuel_type.lower()} '
        # Notification.objects.create(user=supplier,message=message, reference_id=fuel_request.id, action="new_request")
        messages.success(request, f"Successfully Made A Private Order To Our Suppliers")

    return redirect('buyer:accounts')


"""

Proof of payment 

"""


@login_required
def proof_of_payment(request, user_id):
    if request.method == 'POST':
        transaction = Transaction.objects.filter(id=user_id).first()
        if transaction is not None:
            if transaction.pending_proof_of_payment == True:
                messages.warning(request, 'Please wait for the supplier to approve the existing proof of payment')
                return redirect('buyer-transactions')
            else:
                account = Account.objects.filter(buyer_company=request.user.company).first()
                account_history= AccountHistory.objects.create(transaction=transaction,account=account)
                account_history.proof_of_payment = request.FILES.get('proof_of_payment')
                account_history.balance = transaction.expected - transaction.paid
                account_history.save()
                transaction.proof_of_payment = request.FILES.get('proof_of_payment')
                transaction.proof_of_payment_approved = False
                transaction.pending_proof_of_payment == True
                transaction.save()
                messages.success(request, 'Proof of payment successfully uploaded')
                return redirect('buyer-transactions')
        else:
            pass


"""

payment history

"""

def payment_history(request, id):
    form1 = DeliveryScheduleForm()           
    print(request.user.company)
    transaction = Transaction.objects.filter(id=id).first()
    payment_history = AccountHistory.objects.filter(transaction=transaction).all()
    return render(request, 'buyer/payment_history.html', {'payment_history': payment_history, 'form1':form1})

"""

Account Application

"""


@login_required
def account_application(request):
    companies = Company.objects.filter(company_type='SUPPLIER').all()
    for company in companies:
        company.admin = User.objects.filter(company=company, user_type='S_ADMIN').first()
        print(company)
        status = Account.objects.filter(buyer_company=request.user.company, supplier_company=company).exists()
        if status:
            account = Account.objects.filter(buyer_company=request.user.company, supplier_company=company).first()
            if account.is_verified:
                company.account_verified = True
            else:
                company.account_verified = False
            company.account_exist = True
        else:
            company.account_exist = False
    context = {
        'companies': companies
    }
    return render(request, 'buyer/supplier_application.html', context=context)


@login_required
def download_application(request, user_id):
    document = Company.objects.filter(id=user_id).first()
    if document:
        filename = document.application_form.name.split('/')[-1]
        response = HttpResponse(document.application_form, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document Not Found')
        return redirect('accounts-status')
    return response


@login_required
def upload_application(request, user_id):
    if request.method == 'POST':
        supplier = Company.objects.filter(id=user_id).first()
        buyer = request.user.company
        application_form = request.FILES.get('application_form')
        company_documents = request.FILES.get('company_documents')
        Account.objects.create(supplier_company=supplier, buyer_company=buyer, application_document=application_form,
                               id_document=company_documents, applied_by=request.user)
        messages.success(request, 'Application successfully send')
    return redirect('accounts-status')
