import secrets
from datetime import date, datetime, time, timedelta
from operator import attrgetter

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
import pandas as pd
from decimal import *

from accounts.models import Account
from buyer.models import User
from users.models import Activity
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
from .models import FuelRequest, DeliveryBranch
from .models import FuelRequest
from .decorators import user_role, user_permission, ias_user_role

user = get_user_model()
today = date.today()

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
            if current_user.password_reset:
                return redirect("serviceStation:initial-password-change")
            else:
                return redirect("serviceStation:home")
        elif current_user.user_type == 'SUPPLIER':
            if current_user.password_reset:
                return redirect("supplier:initial-password-change")
            else:
                return redirect("available_stock")
        elif current_user.user_type == 'S_ADMIN':
            if current_user.password_reset:
                return redirect("users:initial-password-change")
            else:
                return redirect("users:allocate")
        elif current_user.user_type == 'ZERA':
            return redirect("zeraPortal:dashboard")
        elif current_user.user_type == 'NOIC_STAFF':
            if current_user.password_reset:
                return redirect("noicDepot:initial-password-change")
            else:
                return redirect("noicDepot:accepted_orders")
        elif current_user.user_type == 'NOIC_ADMIN':
            return redirect("noic:dashboard")
        elif current_user.user_type == 'IAS':
            return redirect("buyer:approve_companies")
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
                            if current_user.password_reset:
                                return redirect("serviceStation:initial-password-change")
                            else:
                                return redirect("serviceStation:home")
                        elif current_user.user_type == 'SUPPLIER':
                            if current_user.password_reset:
                                return redirect("supplier:initial-password-change")
                            else:
                                return redirect("fuel-request")
                        elif current_user.user_type == 'S_ADMIN':
                            if current_user.password_reset:
                                return redirect("users:initial-password-change")
                            else:
                                return redirect("users:allocate")
                        elif current_user.user_type == 'ZERA':
                            return redirect("zeraPortal:dashboard")
                        elif current_user.user_type == 'NOIC_STAFF':
                            if current_user.password_reset:
                                return redirect("noicDepot:initial-password-change")
                            else:
                                return redirect("noicDepot:accepted_orders")
                        elif current_user.user_type == 'NOIC_ADMIN':
                            return redirect("noic:dashboard")
                        elif current_user.user_type == 'IAS':
                            return redirect("buyer:approve_companies")
                    # wrong password
                    else:
                        messages.info(request, 'Wrong password.')
                        return redirect('login')
                # user hasn't completed registration yet
                else:
                    messages.info(request, 'Your account is waiting for approval. Please check your email '
                                           'or contact your company administrator.')
                    return redirect('login')
            # throw account not found error
            else:
                messages.info(request, 'Please register first.')
                return redirect('login')
    return render(request, 'buyer/signin.html', context=context)

@login_required
@ias_user_role
def approve_companies(request):
    companies = Company.objects.filter(~Q(company_type='SUPPLIER')).all()
    return render(request, 'buyer/approve_companies.html', {'companies': companies})


def activate_company(request, id):
    company = Company.objects.filter(id=id).first()
    company_rep = User.objects.filter(company=company).first()
    company.is_active = True
    company_rep.is_active = True
    company.is_verified = True
    company.save()
    company_rep.save()
    messages.success(request, f"Company {company.name} and its rep {company_rep.first_name} acivated successfully.")
    return redirect('buyer:approve_companies')

def decline_company(request, id):
    company = Company.objects.filter(id=id).first()
    company_rep = User.objects.filter(company=company).first()
    company.declined = True
    company.save()
    messages.warning(request, f"Company {company.name} and its rep {company_rep.username} declined.")
    return redirect('buyer:approve_companies')
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
    subject = 'ZFMS Registration'
    message = f"Dear {auth_user.first_name}  {auth_user.last_name}. \nYour username is: " \
              f"{auth_user.username}\n\nPlease complete " \
              f"signup here : \n {url} \n. "
    # noinspection PyBroadException
    try:
        msg = EmailMultiAlternatives(subject, message, sender, [f'{auth_user.email}'])
        msg.send()

        messages.success(request, f"{auth_user.first_name}  {auth_user.last_name} has completed first stage of registration successfully.")
        return True
    except Exception:
        messages.warning(request, f"Could not send registration details, please contact ZFMS")
        return False
        messages.success(request, ('Your profile has been successfully updated.'))
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
                    messages.success(auth_user.phone_number, "You have completed your first stage of registration successfully.")
                    auth_user.stage = 'requesting'
                    auth_user.save()

                return render(request, 'buyer/email_send.html')
            else:
                # messages.warning(request, f"Oops , Something Wen't Wrong, Please Try Again")
                return render(request, 'buyer/email_send.html')

        else:
            msg = "Error. We have a user with this user email-id."
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
@user_role
def change_password(request):
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
    context = {
        'title': 'ZFMS | Change Password',
        'num_of_notifications': num_of_notifications,
        'notifications': notifications,
        'password_change': PasswordChange(user=request.user)
    }
    if request.method == 'POST':
        old = request.POST.get('old_password')
        new1 = request.POST.get('new_password1')
        new2 = request.POST.get('new_password2')

        if authenticate(request, username=request.user.username, password=old):
            if new1 != new2:
                messages.error(request, "Passwords don't match.")
                return redirect('bchange-password')
            elif new1 == old:
                messages.error(request, "New password can not be similar to the old one.")
                return redirect('bchange-password')
            elif len(new1) < 8:
                messages.error(request, "Password is too short.")
                return redirect('bchange-password')
            elif new1.isnumeric():
                messages.error(request, "Password can not be entirely numeric.")
            elif not new1.isalnum():
                messages.error(request, "Password should be alphanumeric.")
                return redirect('bchange-password')
            else:
                current_user = request.user
                current_user.set_password(new1)
                current_user.save()
                update_session_auth_hash(request, current_user)

                messages.success(request, 'Password has been successfully changed.')
                return redirect('buyer-profile')
        else:
            messages.error(request, 'Wrong old password, please try again.')
            return redirect('bchange-password')
    return render(request, 'buyer/change_password.html', context=context)


"""

for loading user profile, editing profile and changing password

"""


@login_required()
@user_role
def profile(request):
    compan = Company.objects.filter(id=request.user.company.id).first()
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
    if request.method == 'POST':
        old = request.POST.get('old_password')
        new1 = request.POST.get('new_password1')
        new2 = request.POST.get('new_password2')

        if authenticate(request, username=request.user.username, password=old):
            if new1 != new2:
                messages.error(request, "Passwords don't match.")
                return redirect('buyer-profile')
            else:
                current_user = request.user
                current_user.set_password(new1)
                current_user.save()
                update_session_auth_hash(request, current_user)

                messages.success(request, 'Password successfully changed.')
                return redirect('buyer-profile')
        else:
            messages.error(request, 'Wrong old password, please try again.')
            return redirect('buyer-profile')

    context = {
        'form': PasswordChangeForm(user=request.user),
        'user_logged': request.user,
        'compan': compan,
        'num_of_notifications': num_of_notifications,
        'notifications': notifications
    }
    return render(request, 'buyer/profile.html', context)


"""

The function based view is responsible for showing the buyer request.
The requests shown are those that are not complete and             that have been made buy the buyer.

"""


@login_required()
@user_role
def fuel_request(request):
    user_logged = request.user
    fuel_requests = FuelRequest.objects.filter(name=user_logged, is_complete=False).all()
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
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
    complete_requests = FuelRequest.objects.filter(name=user_logged, is_complete=True).all()

    context = {
        'fuel_requests': fuel_requests,
        'complete_requests': complete_requests,
        'num_of_notifications': num_of_notifications,
        'notifications': notifications
    }

    if request.method == "POST":
        if request.POST.get('start_date') and request.POST.get('end_date') :
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()
            fuel_requests = FuelRequest.objects.filter(name=user_logged, is_complete=False).filter(date__range=[start_date, end_date])
            complete_requests = FuelRequest.objects.filter(name=user_logged, is_complete=True).filter(date__range=[start_date, end_date])  
            
            context = {
                'fuel_requests': fuel_requests,
                'complete_requests': complete_requests,
                'start_date': start_date,
                'end_date': end_date
            }

            return render(request, 'buyer/fuel_request.html', context=context)

        if request.POST.get('export_to_csv')=='csv':
            start_date = request.POST.get('csv_start_date')
            end_date = request.POST.get('csv_end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                fuel_requests = FuelRequest.objects.filter(name=user_logged, is_complete=False).filter(date__range=[start_date, end_date])
                complete_requests = FuelRequest.objects.filter(name=user_logged, is_complete=True).filter(date__range=[start_date, end_date])
            
            fuel_requests = fuel_requests.values('date','delivery_method','payment_method','fuel_type', 'amount')
            complete_requests =  complete_requests.values('date','delivery_method','payment_method','fuel_type', 'amount')
            fields = ['date','delivery_method','payment_method','fuel_type', 'amount']
            
            df_fuel_requests = pd.DataFrame(fuel_requests, columns=fields)
            df_complete_requests = pd.DataFrame(complete_requests, columns=fields)

            df = df_fuel_requests.append(df_complete_requests)
            df.columns = ['Date','Delivery Method','Payment Method','Fuel Type', 'Amount']

            # df = df[['date','noic_depot', 'fuel_type', 'quantity', 'currency', 'status']]
            filename = f'{request.user.company.name}.csv'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - Requests - {today}.csv'
                return response     

        else:
            start_date = request.POST.get('pdf_start_date')
            end_date = request.POST.get('pdf_end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                fuel_requests = FuelRequest.objects.filter(name=user_logged, is_complete=False).filter(date__range=[start_date, end_date])
                complete_requests = FuelRequest.objects.filter(name=user_logged, is_complete=True).filter(date__range=[start_date, end_date]) 

            context = {
                'fuel_requests': fuel_requests,
                'complete_requests': complete_requests,
                'start_date': start_date,
                'date': today,
                'end_date': end_date
            }    

            html_string = render_to_string('buyer/export/export_requests.html', context=context)
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} -Orders - {today}.pdf'
                return response        


    return render(request, 'buyer/fuel_request.html', context=context)


"""

Looking for fuel from suppliers

"""


@login_required
@user_role
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

            messages.success(request, f'Your request has been made. ')

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
@user_role
def dashboard(request):
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
    updates = []
    branches = DeliveryBranch.objects.filter(company=request.user.company).all()
    if request.user.company.is_govnt_org:
        fuel_updates = SuballocationFuelUpdate.objects.filter(~Q(subsidiary__praz_reg_num=None)).all()
        for fuel_update in fuel_updates:
            if fuel_update.diesel_quantity == 0.00 and fuel_update.petrol_quantity == 0.00:
                pass
            else:
                updates.append(fuel_update)
    else:
        fuel_updates = SuballocationFuelUpdate.objects.all()
        for fuel_update in fuel_updates:
            if fuel_update.diesel_quantity == 0.00 and fuel_update.petrol_quantity == 0.00:
                pass
            else:
                updates.append(fuel_update)
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
    updates.sort(key=attrgetter('date', 'time'), reverse=True)
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
                if fuel_request_object.delivery_method.lower() == "delivery":
                    branch_id = int(request.POST.get('d_branch'))
                    branch = DeliveryBranch.objects.filter(id=branch_id).first()
                    fuel_request_object.delivery_address = branch.street_number + " " + branch.street_name + " " + branch.city
                else:
                    fuel_request_object.transporter = request.POST.get('transporter')
                    fuel_request_object.truck_reg = request.POST.get('truck_reg')
                    fuel_request_object.driver = request.POST.get('driver')
                    fuel_request_object.driver_id = request.POST.get('driver_id')
                fuel_request_object.storage_tanks = request.POST.get('storage_tanks')
                fuel_request_object.pump_required = True if request.POST.get('pump_required') == "on" else False
                fuel_request_object.dipping_stick_required = True if request.POST.get(
                    'dipping_stick_required') == "on" else False
                fuel_request_object.meter_required = True if request.POST.get('meter_required') == "on" else False
                fuel_request_object.is_direct_deal = True
                fuel_request_object.last_deal = int(request.POST.get('company_id'))
                fuel_request_object.save()
                current_user = User.objects.filter(subsidiary_id=fuel_request_object.last_deal).first()

            action = "Fuel Request"
            description = f"You have made fuel request of {fuel_request_object.amount} {fuel_request_object.fuel_type}"
            Activity.objects.create(company=request.user.company, user=request.user, action=action,
                                    description=description, reference_id=fuel_request_object.id)
            messages.success(request, f'Kindly note your request has been made. ')
            message = f'{request.user.first_name} {request.user.last_name} made a request of ' \
                      f'{fuel_request_object.amount}L {fuel_request_object.fuel_type.lower()}'
            Notification.objects.create(company=request.user.company, handler_id=15, message=message, user=request.user, reference_id=fuel_request_object.id,
                                        action="new_request")
            return redirect('buyer-dashboard')

        if 'WaitForOffer' in request.POST:
            if form.is_valid():
                fuel_request_object = FuelRequest()
                fuel_request_object.name = request.user
                fuel_request_object.amount = form.cleaned_data['amount']
                fuel_request_object.fuel_type = form.cleaned_data['fuel_type']
                fuel_request_object.payment_method = request.POST.get('fuel_payment_method')
                fuel_request_object.delivery_method = form.cleaned_data['delivery_method']
                if fuel_request_object.delivery_method.lower() == "delivery":
                    branch_id = int(request.POST.get('d_branch'))
                    branch = DeliveryBranch.objects.filter(id=branch_id).first()
                    fuel_request_object.delivery_address = branch.street_number + " " + branch.street_name + " " + branch.city
                else:
                    fuel_request_object.transporter = request.POST.get('transporter')
                    fuel_request_object.truck_reg = request.POST.get('truck_reg')
                    fuel_request_object.driver = request.POST.get('driver')
                    fuel_request_object.driver_id = request.POST.get('driver_id')
                fuel_request_object.storage_tanks = request.POST.get('storage_tanks')
                fuel_request_object.pump_required = True if request.POST.get('pump_required') == "True" else False
                fuel_request_object.dipping_stick_required = True if request.POST.get(
                    'dipping_stick_required') == "True" else False
                fuel_request_object.meter_required = True if request.POST.get('meter_required') == "True" else False
                fuel_request_object.wait = True
                fuel_request_object.save()

            action = "Fuel Request"
            description = f"You have made fuel request of {fuel_request_object.amount} {fuel_request_object.fuel_type}"
            Activity.objects.create(company=request.user.company, user=request.user, action=action,
                                    description=description, reference_id=fuel_request_object.id)
            messages.success(request, f'Fuel request has been submitted successfully and is now awaiting an offer.')
            message = f'{request.user.first_name} {request.user.last_name} made a request of ' \
                      f'{fuel_request_object.amount}L {fuel_request_object.fuel_type.lower()}'
            Notification.objects.create(company=request.user.company, handler_id=15, message=message, user=request.user, reference_id=fuel_request_object.id,
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
                if fuel_request_object.delivery_method.lower() == "delivery":
                    branch_id = int(request.POST.get('d_branch'))
                    branch = DeliveryBranch.objects.filter(id=branch_id).first()
                    fuel_request_object.delivery_address = branch.street_number + " " + branch.street_name + " " + branch.city
                else:
                    fuel_request_object.transporter = request.POST.get('transporter')
                    fuel_request_object.truck_reg = request.POST.get('truck_reg')
                    fuel_request_object.driver = request.POST.get('driver')
                    fuel_request_object.driver_id = request.POST.get('driver_id')
                fuel_request_object.storage_tanks = request.POST.get('storage_tanks')
                fuel_request_object.pump_required = True if request.POST.get('pump_required') == "True" else False
                fuel_request_object.dipping_stick_required = True if request.POST.get(
                    'dipping_stick_required') == "True" else False
                fuel_request_object.meter_required = True if request.POST.get('meter_required') == "True" else False
                fuel_request_object.is_complete = True
                fuel_request_object.save()
                offer_id, response_message = recommend(fuel_request_object)
                if not offer_id:
                    messages.error(request, response_message)
                else:
                    offer = Offer.objects.filter(id=offer_id).first()
                    sub = Subsidiaries.objects.filter(id=offer.supplier.subsidiary_id).first()
                    messages.info(request, "Match found.")

                    action = "Fuel Request"
                    description = f"You have made fuel request of {fuel_request_object.amount} {fuel_request_object.fuel_type}"
                    Activity.objects.create(company=request.user.company, user=request.user, action=action,
                                            description=description, reference_id=fuel_request_object.id)
                    return render(request, 'buyer/dashboard.html',
                                  {'form': form, 'updates': updates, 'offer': offer, 'sub': sub, 'branches' : branches})
    else:
        form = FuelRequestForm
    return render(request, 'buyer/dashboard.html', {'notifications': notifications, 'num_of_notifications': num_of_notifications, 'form': form, 'updates': updates, 'branches' : branches})


"""

Offers


"""


@login_required
def offers(request, id):
    user_permission(request)
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
    selected_request = FuelRequest.objects.filter(id=id).first()
    offers = Offer.objects.filter(request=selected_request).filter(declined=False).all()
    for offer in offers:
        depot = Subsidiaries.objects.filter(id=offer.supplier.subsidiary_id).first()
        account = Account.objects.filter(buyer_company=request.user.company,
                                         supplier_company=offer.supplier.company).first()
        if depot:
            offer.depot_name = depot.name
            offer.depot_address = depot.location
        if account:
            offer.account = account
    offers.order_by('-date', '-time')
    return render(request, 'buyer/offer.html', {'num_of_notifications': num_of_notifications, 'notifications': notifications, 'offers': offers})


"""

Offer Handlers

"""


@login_required
def new_offer(request, id):
    user_permission(request)
    offers_available = Offer.objects.filter(id=id).all()
    return render(request, 'buyer/new_offer.html', {'offers': offers_available})


@login_required
def new_fuel_offer(request, id):
    user_permission(request)
    offers_present = Offer.objects.filter(id=id).all()
    for offer in offers_present:
        depot = Subsidiaries.objects.filter(id=offer.supplier.subsidiary_id).first()
    return render(request, 'buyer/new_offer.html', {'offers': offers_present, 'depot': depot})


@login_required
def accept_offer(request, id):
    user_permission(request)
    offer = Offer.objects.filter(id=id).first()
    account = Account.objects.filter(buyer_company=request.user.company, supplier_company=offer.supplier.company,
                                     is_verified=True).first()
    if account is not None:
        if offer.transport_fee is not None:
            expected = int((Decimal(offer.quantity) * offer.price) + Decimal(offer.transport_fee))
        else:
            expected = int(Decimal(offer.quantity) * offer.price)
        Transaction.objects.create(offer=offer, buyer=request.user, supplier=offer.supplier, is_complete=False,
                                   expected=expected)
        FuelRequest.objects.filter(id=offer.request.id).update(is_complete=True)
        offer.is_accepted = True
        offer.save()

        message = f'{offer.request.name.first_name} {offer.request.name.last_name} accepted your offer of {offer.quantity}L {offer.request.fuel_type.lower()} at ${offer.price}'
        Notification.objects.create(message=message, user=offer.supplier, reference_id=offer.id,
                                    action="offer_accepted")

        action = "Accepting Offer"
        description = f"You have accepted offer of {offer.quantity}L {offer.request.fuel_type}"
        Activity.objects.create(company=request.user.company, user=request.user, action=action, description=description,
                                reference_id=offer.id)
        messages.success(request, "Accepted offer successfully.")
        return redirect("buyer-transactions")
    else:
        messages.info(request,
                      f"You have no account with {offer.supplier.company.name} yet, please apply or wait for approval if you have already applied.")
        return redirect("accounts-status")


@login_required
def reject_offer(request, id):
    user_permission(request)
    offer = Offer.objects.filter(id=id).first()
    offer.declined = True
    offer.save()
    my_request = FuelRequest.objects.filter(id=offer.request.id).first()
    my_request.wait = True
    my_request.is_complete = False
    my_request.save()

    action = "Rejecting Offer"
    description = f"You have rejected offer of {offer.quantity}L {offer.request.fuel_type}"
    Activity.objects.create(company=request.user.company, user=request.user, action=action, description=description,
                            reference_id=offer.id)

    message = f'{offer.request.name.first_name} {offer.request.name.last_name} rejected your offer of {offer.quantity}L {offer.request.fuel_type.lower()} at ${offer.price}'
    Notification.objects.create(message=message, user=offer.supplier, reference_id=offer.id, action="offer_rejected")

    # FuelRequest.objects.filter(id=offer.request.id).update(is_complete=True)
    messages.success(request,
                     "Your request has been saved and as offer updates are coming you will receive notifications.")
    return redirect("buyer-fuel-request")


"""

Transaction Handlers

"""


@login_required
@user_role
def transactions(request):

    buyer = request.user
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
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
            # transaction.address = subsidiary.location
        from supplier.models import UserReview
        transaction.review = UserReview.objects.filter(transaction=transaction).first()
        # if transaction.is_complete == True:
        #     complete_trans.append(transaction)
        # else:
        #     in_complete_trans.append(transaction)
    complete_trans = all_transactions.filter(is_complete=True)
    in_complete_trans = all_transactions.filter(is_complete=False)
        
    # in_complete_trans.sort(key=attrgetter('date', 'time'), reverse=True)
    # complete_trans.sort(key=attrgetter('date', 'time'), reverse=True)
    
    context = {
        'transactions': complete_trans.order_by('-date', '-time'),
        'incomplete_transactions': in_complete_trans.order_by('-date', '-time'),
        'subsidiary': Subsidiaries.objects.filter(),
        'notifications': notifications,
        'num_of_notifications': num_of_notifications,
        'all_transactions': AccountHistory.objects.filter().order_by('-date', '-time')
    }

    if request.method == "POST":
        if request.POST.get('start_date') and request.POST.get('end_date') :
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()

            all_transactions = Transaction.objects.filter(buyer=buyer).filter(date__range=[start_date, end_date])
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
                    # transaction.address = subsidiary.location
                from supplier.models import UserReview
                transaction.review = UserReview.objects.filter(transaction=transaction).first()
                # if transaction.is_complete == True:
                #     complete_trans.append(transaction)
                # else:
                #     in_complete_trans.append(transaction)
            complete_trans = all_transactions.filter(is_complete=True)
            in_complete_trans = all_transactions.filter(is_complete=False)
                
        
            context = {
                'transactions': complete_trans.order_by('-date', '-time'),
                'incomplete_transactions': in_complete_trans.order_by('-date', '-time'),
                'subsidiary': Subsidiaries.objects.filter(),
                'all_transactions': AccountHistory.objects.filter().order_by('-date', '-time'),
                'start_date': start_date,
                'end_date': end_date

            }


            return render(request, 'buyer/transactions.html', context=context)


        if request.POST.get('export_to_csv')=='csv':
            start_date = request.POST.get('csv_start_date')
            end_date = request.POST.get('csv_end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                all_transactions = Transaction.objects.filter(buyer=buyer).filter(date__range=[start_date, end_date])
            
            complete_trans = all_transactions.filter(is_complete=True)
            in_complete_trans = all_transactions.filter(is_complete=False)    
            
            complete_trans = complete_trans.values('date','time', 'supplier__company__name',
             'offer__request__fuel_type', 'offer__request__amount', 'is_complete')
            in_complete_trans =  in_complete_trans.values('date','time', 'supplier__company__name',
             'offer__request__fuel_type', 'offer__request__amount', 'is_complete')
            fields = ['date','time', 'supplier__company__name', 'offer__request__fuel_type', 'offer__request__amount', 'is_complete']
            
            df_complete_trans = pd.DataFrame(complete_trans, columns=fields)
            df_in_complete_trans = pd.DataFrame(in_complete_trans, columns=fields)

            df = df_complete_trans.append(df_in_complete_trans)
            df.columns = ['Date','Time', 'Supplier', 'Fuel Type', 'Quantity', 'Complete']

            # df = df[['date','noic_depot', 'fuel_type', 'quantity', 'currency', 'status']]
            filename = f'{request.user.company.name}.csv'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - Transactions - {today}.csv'
                return response     

        if request.POST.get('export_to_pdf') == 'pdf':
            start_date = request.POST.get('pdf_start_date')
            end_date = request.POST.get('pdf_end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                all_transactions = Transaction.objects.filter(buyer=buyer).filter(date__range=[start_date, end_date])
                
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
                    # transaction.address = subsidiary.location
                from supplier.models import UserReview
                transaction.review = UserReview.objects.filter(transaction=transaction).first()
                # if transaction.is_complete == True:
                #     complete_trans.append(transaction)
                # else:
                #     in_complete_trans.append(transaction)
            complete_trans = all_transactions.filter(is_complete=True)
            in_complete_trans = all_transactions.filter(is_complete=False)
        
            context = {
                'transactions': complete_trans.order_by('-date', '-time'),
                'incomplete_transactions': in_complete_trans.order_by('-date', '-time'),
                'subsidiary': Subsidiaries.objects.filter(),
                'all_transactions': AccountHistory.objects.filter().order_by('-date', '-time'),
                'date': today,
                'start_date': start_date,
                'end_date': end_date
            }

            html_string = render_to_string('buyer/export/export_transactions.html', context=context)
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} - Transactions - {today}.pdf'
                return response        


        if request.POST.get('buyer_id') is not None:
            buyer_transactions = AccountHistory.objects.filter(
                transaction__buyer__company__id=int(request.POST.get('buyer_id')),
                transaction__supplier__company__id=int(request.POST.get('supplier_id')),
            )

            html_string = render_to_string('supplier/export.html', {'transactions': buyer_transactions})
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
                company_type='SUPPLIER',
                company=tran.supplier.company,
                transaction=tran,
                depot=Subsidiaries.objects.filter(id=tran.supplier.subsidiary_id).first(),
                comment=request.POST.get('comment')
            )
            messages.success(request, 'Transaction successfully reviewed.')
            return redirect('buyer-transactions')

    return render(request, 'buyer/transactions.html', context=context)


@login_required
def transactions_review_delete(request, transaction_id):
    user_permission(request)
    from supplier.models import UserReview
    rev = UserReview.objects.filter(id=transaction_id).first()
    rev.delete()
    messages.success(request, 'Review successfully deleted.')
    return redirect("buyer-transactions")


@login_required
def transaction_review_edit(request, id):
    user_permission(request)
    from supplier.models import UserReview
    review = UserReview.objects.filter(id=id).first()
    if request.method == "POST":
        review.rating = int(request.POST.get('rating'))
        review.comment = request.POST.get('comment')
        review.save()
        messages.success(request, 'Review successfully edited')
    return redirect("buyer-transactions")


"""

Invoice Handlers
 
"""


@login_required
def invoice(request, id):
    user_permission(request)
    buyer = request.user
    transactions_availabe = Transaction.objects.filter(buyer=buyer, id=id).first()

    context = {
        'transactions': transactions_availabe
    }

    pdf = render_to_pdf('buyer/invoice.html', context)
    return HttpResponse(pdf, content_type='application/pdf')


@login_required
def view_invoice(request, id):
    user_permission(request)
    buyer = request.user
    transaction = Transaction.objects.filter(buyer=buyer, id=id).all()
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


@login_required()
def view_release_note(request, id):
    user_permission(request)
    payment = AccountHistory.objects.filter(id=id).first()
    payment.quantity = float(payment.value) / float(payment.transaction.offer.price)
    context = {
        'payment': payment
    }
    return render(request, 'buyer/release_note.html', context=context)


@login_required
@user_role
def delivery_schedules(request):
    completed_schedules = []
    pending_schedules =[]
    schedules = DeliverySchedule.objects.filter(transaction__buyer=request.user).all()
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()

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
            if schedule.transaction.offer.collection_address.strip() == "":
                depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                schedule.delivery_address = depot.location
            else:
                if schedule.transaction.offer.collection_address != None:
                    schedule.delivery_address = schedule.transaction.offer.collection_address
                else:
                    depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                    schedule.delivery_address = depot.location
        
    completed_schedules = schedules.filter(confirmation_date__isnull=False)
    for schedule in completed_schedules:
        schedule.subsidiary = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
    pending_schedules = schedules.filter(confirmation_date__isnull=True)
    for schedule in pending_schedules:
        schedule.subsidiary = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()


    context = {
        'pending_schedules': pending_schedules,
        'completed_schedules': completed_schedules,
        'num_of_notifications': num_of_notifications,
        'notifications': notifications
       }

    if request.method == 'POST':
        if request.POST.get('delivery_id'):
            confirmation_date = request.POST.get('delivery_date')
            delivery_id = int(request.POST.get('delivery_id'))

            schedule = DeliverySchedule.objects.filter(id=delivery_id).first()
            schedule.confirmation_date = confirmation_date
            schedule.save()
            messages.success(request, 'Delivery successfully confirmed.')
            message = f"Delivery confirmed for {schedule.transaction.buyer.company}, Click to view confirmation document"
            Notification.objects.create(user=request.user, action='DELIVERY', message=message, reference_id=schedule.id)
            return redirect('delivery-schedule')


        if request.POST.get('start_date') and request.POST.get('end_date') :
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()

            schedules = DeliverySchedule.objects.filter(transaction__buyer=request.user).filter(date__range=[start_date, end_date])

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
                    if schedule.transaction.offer.collection_address.strip() == "":
                        depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                        schedule.delivery_address = depot.location
                    else:
                        if schedule.transaction.offer.collection_address != None:
                            schedule.delivery_address = schedule.transaction.offer.collection_address
                        else:
                            depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                            schedule.delivery_address = depot.location      
            
            completed_schedules = schedules.filter(confirmation_date__isnull=False)
            pending_schedules = schedules.filter(confirmation_date__isnull=True) 
            
            context = {
                'start_date': start_date,
                'end_date': end_date,
                'pending_schedules': pending_schedules,
                'completed_schedules': completed_schedules
            }

            return render(request, 'buyer/delivery_schedules.html', context=context)
                

        if request.POST.get('export_to_csv')=='csv':
            start_date = request.POST.get('csv_start_date')
            end_date = request.POST.get('csv_end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                completed_schedules = DeliverySchedule.objects.filter(transaction__buyer=request.user).filter(confirmation_date__isnull=False).filter(date__range=[start_date, end_date])
                pending_schedules = DeliverySchedule.objects.filter(transaction__buyer=request.user).filter(confirmation_date__isnull=True).filter(date__range=[start_date, end_date])
            
            completed_schedules = completed_schedules.values('date','transaction__supplier__company__name', 'transaction__offer__request__delivery_address', 'transaction__offer__request__fuel_type',
             'delivery_quantity', 'transport_company', 'driver_name', 'id_number', 'vehicle_reg' )
            pending_schedules =  pending_schedules.values('date','transaction__supplier__company__name', 'transaction__offer__request__delivery_address', 'transaction__offer__request__fuel_type',
             'delivery_quantity', 'transport_company', 'driver_name', 'id_number', 'vehicle_reg' )
            fields = ['date','transaction__supplier__company__name', 'transaction__offer__request__delivery_address', 'transaction__offer__request__fuel_type',
             'delivery_quantity', 'transport_company', 'driver_name', 'id_number', 'vehicle_reg' ]
            
            df_completed_schedules = pd.DataFrame(completed_schedules, columns=fields)
            df_pending_schedules = pd.DataFrame(pending_schedules, columns=fields)

            df = df_completed_schedules.append(df_pending_schedules)
            df.columns = ['Date','Supplier', 'Delivery Address', 'Fuel Type',
             'Deliver Qty.', 'Transporter Company', 'Driver Name', 'Id Number', 'Vehicle Reg' ]

            # df = df[['date','noic_depot', 'fuel_type', 'quantity', 'currency', 'status']]
            filename = f'{request.user.company.name}'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} -Delivery Schedules -{today}.csv'
                return response     

        else:
            start_date = request.POST.get('pdf_start_date')
            end_date = request.POST.get('pdf_end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                completed_schedules = DeliverySchedule.objects.filter(transaction__buyer=request.user).filter(confirmation_date__isnull=False).filter(date__range=[start_date, end_date])
                pending_schedules = DeliverySchedule.objects.filter(transaction__buyer=request.user).filter(confirmation_date__isnull=True).filter(date__range=[start_date, end_date])

            context = {
                'start_date': start_date,
                'end_date': end_date,
                'pending_schedules': pending_schedules,
                'date': today,
                'completed_schedules': completed_schedules
            }


            html_string = render_to_string('buyer/export/export_delivery_schedules.html', context=context)
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} -Orders - {today}.pdf'
                return response        


    return render(request, 'buyer/delivery_schedules.html', context=context)


@login_required()
def delivery_schedule(request, id):
    user_permission(request)
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


@login_required()
@user_role
def accounts(request):
    form = FuelRequestForm(request.POST)
    accounts_available = Account.objects.filter(buyer_company=request.user.company).all()
    fuel_orders = FuelRequest.objects.filter(private_mode=True).all().order_by('date')
    order_nums, latest_orders = total_requests(request.user.company)
    total_costs = transactions_total_cost(request.user)
    offers_count_all, offers_count_today = total_offers(request.user)
    branches = DeliveryBranch.objects.filter(company=request.user.company).all()
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
    return render(request, 'buyer/accounts.html',
                  {'notifications': notifications, 'num_of_notifications': num_of_notifications, 'branches': branches, 'form': form, 'accounts': accounts_available, 'fuel_orders': fuel_orders, 'order_nums': order_nums,
                   'latest_orders': latest_orders, 'total_costs': total_costs, 'offers_count_all': offers_count_all,
                   'offers_count_today': offers_count_today})


"""

Direct Request

"""


@login_required()
def make_direct_request(request, id):
    user_permission(request)
    """
    Function To Make Direct Requests With A Particular Supplier
    """
    if request.method == "POST":
        supplier = User.objects.filter(company__id=id).first()
        if supplier:
            fuel_request_object = FuelRequest.objects.create(
                name=request.user,
                is_direct_deal=True,
                fuel_type=request.POST.get('fuel_type'),
                amount=request.POST.get('amount'),
                payment_method=request.POST.get('currency'),
                delivery_method=request.POST.get('delivery_method'),
                supplier_company=supplier.company,
                wait=True,
                private_mode=True,
            )
            if fuel_request_object.delivery_method.lower() == "delivery":
                branch_id = int(request.POST.get('d_branch'))
                branch = DeliveryBranch.objects.filter(id=branch_id).first()
                fuel_request_object.delivery_address = branch.street_number + " " + branch.street_name + " " + branch.city
            else:
                fuel_request_object.transporter = request.POST.get('transporter')
                fuel_request_object.truck_reg = request.POST.get('truck_reg')
                fuel_request_object.driver = request.POST.get('driver')
                fuel_request_object.driver_id = request.POST.get('driver_id')
            fuel_request_object.storage_tanks = request.POST.get('storage_tanks')
            fuel_request_object.pump_required = True if request.POST.get('pump_required') == "on" else False
            fuel_request_object.dipping_stick_required = True if request.POST.get(
                'dipping_stick_required') == "on" else False
            fuel_request_object.meter_required = True if request.POST.get('meter_required') == "on" else False
            fuel_request_object.save()
            messages.success(request, f"Successfully made an order to {supplier.company.name}.")
            message = f'{request.user.company.name.title()} made a request of ' \
                      f'{fuel_request_object.amount}L {fuel_request_object.fuel_type.lower()}'
            Notification.objects.create(company=request.user.company, handler_id=16, user=request.user, message=message, reference_id=fuel_request_object.id,
                                        action="new_request")
            
            
        else:
            messages.error(request, f"Supplier not found.")

    return redirect('buyer:accounts')


"""

Edit Account Details

"""


@login_required()
def edit_account_details(request, id):
    user_permission(request)
    account = Account.objects.filter(id=id).first()
    if request.method == "POST":
        address = request.POST.get('address')
        account.buyer_company.address = address
        account.buyer_company.save()
        messages.success(request, f"Successfully made changes to account details.")
    return redirect('buyer:accounts')


"""

Make private request

"""


@login_required()
@user_role
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
            amount=request.POST.get('amount'),
            payment_method=request.POST.get('currency'),
            delivery_method=request.POST.get('delivery_method'),
            # supplier=account.supplier_company,
            private_mode=True,
            wait=True,
        )
        if fuel_request_object.delivery_method.lower() == "delivery":
            branch_id = int(request.POST.get('d_branch'))
            branch = DeliveryBranch.objects.filter(id=branch_id).first()
            fuel_request_object.delivery_address = branch.street_number + " " + branch.street_name + " " + branch.city
        else:
            fuel_request_object.transporter = request.POST.get('transporter')
            fuel_request_object.truck_reg = request.POST.get('truck_reg')
            fuel_request_object.driver = request.POST.get('driver')
            fuel_request_object.driver_id = request.POST.get('driver_id')
        fuel_request_object.storage_tanks = request.POST.get('storage_tanks')
        fuel_request_object.pump_required = True if request.POST.get('pump_required') == "on" else False
        fuel_request_object.dipping_stick_required = True if request.POST.get(
            'dipping_stick_required') == "on" else False
        fuel_request_object.meter_required = True if request.POST.get('meter_required') == "on" else False
        fuel_request_object.save()
        
        messages.success(request, f"Successfully made a private order to our suppliers.")

    return redirect('buyer:accounts')


"""

Proof of payment 

"""


@login_required
def proof_of_payment(request, id):
    user_permission(request)
    if request.method == 'POST':
        transaction = Transaction.objects.filter(id=id).first()
        if transaction is not None:
            if transaction.pending_proof_of_payment == True:
                messages.error(request, 'Please wait for the supplier to approve the existing proof of payment.')
                return redirect('buyer-transactions')
            else:
                account = Account.objects.filter(buyer_company=request.user.company).first()
                account_history = AccountHistory.objects.create(transaction=transaction, sord_number=None, account=account)
                account_history.proof_of_payment = request.FILES.getlist('proof_of_payment')
                account_history.balance = transaction.expected - transaction.paid
                account_history.save()
                transaction.proof_of_payment = request.FILES.getlist('proof_of_payment')
                transaction.proof_of_payment_approved = False
                transaction.pending_proof_of_payment = True
                transaction.save()

                action = "Uploading Proof of Payment"
                description = f"You have uploaded proof of payment for transaction of {transaction.offer.quantity}L {transaction.offer.request.fuel_type}"
                Activity.objects.create(company=request.user.company, user=request.user, action=action,
                                        description=description, reference_id=account_history.id)
                messages.success(request, 'Proof of payment successfully uploaded.')
                return redirect('buyer-transactions')
        else:
            pass


@login_required()
def delivery_note(request, id):
    user_permission(request)
    if request.method == 'POST':
        payment = AccountHistory.objects.filter(id=id).first()
        if payment is not None:
            payment.delivery_date = request.POST['delivery_date']
            payment.save()

            action = "Uploading Delivery Note"
            description = f"You have uploaded d-note for transaction of {payment.transaction.offer.quantity}L {payment.transaction.offer.request.fuel_type}"
            Activity.objects.create(company=request.user.company, user=request.user, action=action,
                                    description=description, reference_id=payment.id)
            messages.success(request, 'Delivery note successfully uploaded.')
            return redirect(f'/buyer/payment_release_notes/{payment.transaction.id}')
        else:
            pass


@login_required()
def download_release_note(request, id):
    user_permission(request)
    document = AccountHistory.objects.filter(id=id).first()
    if document:
        filename = document.release_note.name.split('/')[-1]
        response = HttpResponse(document.release_note, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.error(request, 'Document not found.')
        return redirect(f'/buyer:payment_release_notes/{document.transaction.id}')
    return response


@login_required()
def download_d_note(request, id):
    user_permission(request)
    payment = AccountHistory.objects.filter(id=id).first()
    payment.quantity = float(payment.value) / float(payment.transaction.offer.price)
    payment.depot = Subsidiaries.objects.filter(id=payment.transaction.supplier.subsidiary_id).first()
    context = {
        'payment': payment
    }
    return render(request, 'buyer/delivery_note.html', context=context)

@login_required()
def download_pop(request, id):
    user_permission(request)
    transaction = Transaction.objects.filter(id=id).first()
    document = AccountHistory.objects.filter(transaction=transaction).first()
    if document:
        filename = document.proof_of_payment.name.split('/')[-1]
        response = HttpResponse(document.proof_of_payment, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.error(request, 'Document not found.')
        response = redirect('buyer-transactions')
    return response    


"""

payment history

"""


@login_required()
def payment_history(request, id):
    user_permission(request)
    form1 = DeliveryScheduleForm()
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
    transaction = Transaction.objects.filter(id=id).first()
    payment_history = AccountHistory.objects.filter(transaction=transaction).all()
    return render(request, 'buyer/payment_history.html', {'notifications': notifications, 'num_of_notifications': num_of_notifications, 'payment_history': payment_history, 'form1': form1})


@login_required()
def payment_release_notes(request, id):
    user_permission(request)
    form1 = DeliveryScheduleForm()
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
    transaction = Transaction.objects.filter(id=id).first()
    payment_history = AccountHistory.objects.filter(transaction=transaction).all()
    return render(request, 'buyer/payment_and_rnote.html', {'notifications': notifications, 'num_of_notifications': num_of_notifications, 'payment_history': payment_history, 'form1': form1})


"""

Account Application

"""


@login_required
def account_application(request):
    user_permission(request)
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
    companies = Company.objects.filter(company_type='SUPPLIER').all()
    for company in companies:
        company.admin = User.objects.filter(company=company, user_type='S_ADMIN').first()
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
        'companies': companies,
        'num_of_notifications': num_of_notifications,
        'notifications': notifications
    }
    return render(request, 'buyer/supplier_application.html', context=context)


@login_required
def download_application(request, id):
    user_permission(request)
    company = Company.objects.filter(id=id).first()
    if company.application_form:
        filename = company.application_form.name.split('/')[-1]
        response = HttpResponse(company.application_form, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.info(request, f'Document not found, please wait for {company.name} to upload application form.')
        return redirect('accounts-status')
    return response


@login_required
def upload_application(request, id):
    user_permission(request)
    if request.method == 'POST':
        supplier = Company.objects.filter(id=id).first()
        buyer = request.user.company
        application_form = request.FILES.get('application_form')
        ids = request.FILES.get('company_documents')
        cr14 = request.FILES.get('cr14')
        cr6 = request.FILES.get('cr6')
        cert_of_inco = request.FILES.get('cert_of_inco')
        tax_clearance = request.FILES.get('tax_clearance')
        proof_of_residence = request.FILES.get('proof_of_residence')
        Account.objects.create(supplier_company=supplier, buyer_company=buyer, application_document=application_form,
                               id_document=ids, applied_by=request.user, proof_of_residence=proof_of_residence,
                               cr14=cr14,
                               cr6=cr6, tax_clearance=tax_clearance, cert_of_inco=cert_of_inco)
        messages.success(request, 'Application successfully sent.')
    return redirect('accounts-status')


@login_required()
@user_role
def company_profile(request):
    compan = Company.objects.filter(id=request.user.company.id).first()

    if request.method == 'POST':
        compan.name = request.POST['name']
        compan.address = request.POST['address']
        compan.destination_bank = request.POST['destination_bank']
        compan.account_number = request.POST['account_number']
        compan.save()
        messages.success(request, 'Company profile updated successfully.')
        return redirect('buyer-profile')


@login_required()
@user_role
def activity(request):
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
    current_activities = Activity.objects.filter(user=request.user, date=today).all()
    filtered_activities = None
    for activity in current_activities:
        if activity.action == 'Fuel Request':
            activity.request_object = FuelRequest.objects.filter(id=activity.reference_id).first()
        elif activity.action == 'Accepting Offer':
            activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()
        elif activity.action == 'Rejecting Offer':
            activity.roffer_object = Offer.objects.filter(id=activity.reference_id).first()
    activities = Activity.objects.exclude(date=today).filter(user=request.user)
    for activity in activities:
        if activity.action == 'Fuel Request':
            activity.request_object = FuelRequest.objects.filter(id=activity.reference_id).first()
        elif activity.action == 'Accepting Offer':
            activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()
        elif activity.action == 'Rejecting Offer':
            activity.roffer_object = Offer.objects.filter(id=activity.reference_id).first()

    if request.method == "POST":
        if request.POST.get('start_date') and request.POST.get('end_date') :
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()

            filtered_activities = Activity.objects.filter(user=request.user, date=today).filter(date__range=[start_date, end_date])
            for activity in filtered_activities:
                if activity.action == 'Fuel Request':
                    activity.request_object = FuelRequest.objects.filter(id=activity.reference_id).first()
                elif activity.action == 'Accepting Offer':
                    activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()
                elif activity.action == 'Rejecting Offer':
                    activity.roffer_object = Offer.objects.filter(id=activity.reference_id).first()

            context = {
                'filtered_activities': filtered_activities,
                'activities' : activities,
                'current_activities' : current_activities,
                'start_date': start_date,
                'end_date': end_date
            }


            return render(request, 'buyer/activity.html', context=context)


        if request.POST.get('export_to_csv')=='csv':
            start_date = request.POST.get('csv_start_date')
            end_date = request.POST.get('csv_end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                filtered_activities = Activity.objects.filter(user=request.user, date=today).filter(date__range=[start_date, end_date])
                
            fields = ['date','time', 'user__first_name','user__last_name', 'action', 'description']

            if not filtered_activities:
                current_activities = current_activities.values('date','time', 'user__first_name','user__last_name',
                'action', 'description')
                activities =  activities.values('date','time', 'user__first_name','user__last_name',
                'action', 'description')
                
                df_current_activities = pd.DataFrame(current_activities, columns=fields)
                df_activities = pd.DataFrame(activities, columns=fields)

                df = df_current_activities.append(df_activities)
            else:
                filtered_activities = filtered_activities.values('date','time', 'user__first_name','user__last_name',
                'action', 'description')
                
                df = pd.DataFrame(filtered_activities, columns=fields)
                    

            df.columns = ['Date','Time', 'First Name', 'Last Name', 'Action', 'Description']
            filename = f'{request.user.company.name}'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - Activities - {today}.csv'
                return response     

        else:
            start_date = request.POST.get('pdf_start_date')
            end_date = request.POST.get('pdf_end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                filtered_activities = Activity.objects.filter(user=request.user, date=today).filter(date__range=[start_date, end_date])

            if filtered_activities:
                for activity in filtered_activities:
                    if activity.action == 'Fuel Request':
                        activity.request_object = FuelRequest.objects.filter(id=activity.reference_id).first()
                    elif activity.action == 'Accepting Offer':
                        activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()
                    elif activity.action == 'Rejecting Offer':
                        activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()

            context = {
                'filtered_activities': filtered_activities,
                'activities' : activities,
                'current_activities' : current_activities,
                'start_date': start_date,
                'date': today,
                'end_date': end_date
            }

            html_string = render_to_string('buyer/export/export_activities.html', context=context)
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} - Activities - {today}.pdf'
                return response        


    return render(request, 'buyer/activity.html', {'notifications': notifications, 'num_of_notifications': num_of_notifications, 'activities': activities, 'current_activities': current_activities,
    'filtered_activities':filtered_activities})


'''Handling Delivery Branches'''


@login_required
def delivery_branches(request):
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).count()
    branches = DeliveryBranch.objects.filter(company=request.user.company).all()
    return render(request, 'buyer/delivery_branches.html', {'notifications': notifications, 'num_of_notifications': num_of_notifications, 'branches' : branches})


@login_required()
def create_branch(request):
    if request.method == 'POST':
        name = request.POST['branch_name']
        street_name = request.POST['street_name']
        street_number = request.POST['street_number']
        city = request.POST['city']
        description = request.POST['description']
        check_name = DeliveryBranch.objects.filter(name=name, company=request.user.company).exists()
        if check_name:
            messages.error(request, 'You already have a branch with a similar name.')
            return redirect('buyer:delivery-branches')
        else:
            DeliveryBranch.objects.create(name=name, street_name=street_name, street_number=street_number, city=city,
            company=request.user.company, description=description)
            messages.success(request, 'Branch successfully created.')
            return redirect('buyer:delivery-branches')

        
@login_required()
def edit_branch(request, id):
    user_permission(request)
    if request.method == 'POST':
        branch = DeliveryBranch.objects.filter(id=id).first()
        branch.street_name = request.POST['street_name']
        branch.street_number = request.POST['street_number']
        branch.city = request.POST['city']
        branch.description = request.POST['description']
        branch.save()
        messages.success(request, 'Branch details updated successfully.')
        return redirect('buyer:delivery-branches')



def download_proof(request, id):
    document = AccountHistory.objects.filter(id=id).first()
    if document:
        filename = document.proof_of_payment.name.split('/')[-1]
        response = HttpResponse(document.proof_of_payment, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.error(request, 'Document not found.')
        return redirect('buyer:activity')
    return response


def notication_handler(request, id):
    my_handler = id
    if my_handler == 10:
        notifications = Notification.objects.filter(handler_id=my_handler).all()
        for notification in notifications:
            notification.is_read = True
            notification.save()
        return redirect('buyer:buyer-fuel-request')
    else:
        notifications = Notification.objects.filter(handler_id=my_handler).all()
        for notification in notifications:
            notification.is_read = True
            notification.save()
        return redirect('buyer:buyer-fuel-request')

def notication_reader(request):
    notifications = Notification.objects.filter(company=request.user.company).filter(~Q(action="new_request")).filter(is_read=False).all()
    for notification in notifications:
        notification.is_read = True
        notification.save()
    return redirect('buyer:dashboard')

@login_required()
def view_confirmation_doc(request, id):
    user_permission(request)
    payment = AccountHistory.objects.filter(delivery_schedule__id=id).first()
    payment.quantity = float(payment.value) / float(payment.transaction.offer.price)
    payment.depot = Subsidiaries.objects.filter(id=payment.transaction.supplier.subsidiary_id).first()
    context = {
        'payment': payment
    }
    return render(request, 'buyer/delivery_note.html', context=context)