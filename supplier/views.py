from decimal import *
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from django.template.loader import render_to_string
from weasyprint import HTML
import pandas as pd

from accounts.models import Account, AccountHistory
from buyer.forms import BuyerUpdateForm
from buyer.models import DeliveryBranch
from buyer.utils import render_to_pdf
from company.models import CompanyFuelUpdate
from fuelUpdates.models import SordCompanyAuditTrail
from notification.models import Notification
from users.models import Audit_Trail, SordActionsAuditTrail, Activity
from whatsapp.helper_functions import send_message
from .decorators import user_role, user_permission
from .forms import PasswordChange, CreateCompany, OfferForm
from .lib import *

User = get_user_model()

# today's date
today = date.today()

'''
user registration and login functions
'''


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
                        selected_company = Company.objects.filter(name=request.POST.get('company')).first()
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
                            my_admin = User.objects.filter(company=selected_company, user_type='S_ADMIN').first()
                            if my_admin is not None:
                                return render(request, 'supplier/final_registration.html', {'my_admin': my_admin})
                            else:
                                # user.is_active = True
                                # user.user_type = 'S_ADMIN'
                                # user.is_waiting = False
                                # user.stage = 'menu'
                                # user.save()
                                return render(request, 'supplier/final_reg.html',
                                              {'selected_company': selected_company})
                    else:
                        if user.user_type == 'SUPPLIER':
                            user.delete()
                            return render(request, 'supplier/company_not_existing.html')
                        else:
                            selected_company = Company.objects.create(name=request.POST.get('company'))
                            user.is_active = False
                            user.is_waiting = True
                            selected_company.save()
                            user.company = selected_company
                            user.is_waiting = True
                            user.save()
                            TokenAuthentication.objects.filter(user=user).update(used=True)
                            return redirect('supplier:create_company', id=user.id)

            else:
                return render(request, 'supplier/verify.html',
                              {'form': form, 'industries': industries, 'companies': companies, 'jobs': job_titles})
        else:
            messages.warning(request, 'This link has been used before.')
            return redirect('buyer-register')

    else:
        messages.warning(request, 'Wrong verification token, kindly follow the link send in the email.')
        return redirect('login')

    return render(request, 'supplier/verify.html',
                  {'form': form, 'industries': industries, 'companies': companies, 'jobs': job_titles})


@login_required
@user_role
def initial_password_change(request):
    if request.method == 'POST':
        password1 = request.POST['new_password1']
        password2 = request.POST['new_password2']
        if password1 != password2:
            messages.warning(request, "Passwords don't match.")
            return redirect('supplier:initial-password-change')
        elif len(password1) < 8:
            messages.warning(request, "Password is too short.")
            return redirect('supplier:initial-password-change')
        elif password1.isnumeric():
            messages.warning(request, "Password can not be entirely numeric.")
            return redirect('supplier:initial-password-change')
        elif not password1.isalnum():
            messages.warning(request, "Password should be alphanumeric.")
            return redirect('supplier:initial-password-change')
        else:
            user = request.user
            user.set_password(password1)
            user.password_reset = False
            user.save()
            update_session_auth_hash(request, user)

            messages.success(request, 'Password successfully changed.')
            return redirect('available_stock')
    return render(request, 'supplier/initial_pass_change.html')


@login_required()
@user_role
def change_password(request):
    context = {
        'title': 'ZFMS | Change Password',
        'password_change': PasswordChange(user=request.user)
    }
    if request.method == 'POST':
        old = request.POST.get('old_password')
        new1 = request.POST.get('new_password1')
        new2 = request.POST.get('new_password2')

        if authenticate(request, username=request.user.username, password=old):
            if new1 != new2:
                messages.warning(request, "Passwords don't match.")
                return redirect('change-password')
            elif new1 == old:
                messages.warning(request, "New password can not be similar to the old one.")
                return redirect('change-password')
            elif len(new1) < 8:
                messages.warning(request, "Password is too short.")
                return redirect('change-password')
            elif new1.isnumeric():
                messages.warning(request, "Password can not be entirely numeric.")
                return redirect('change-password')
            elif not new1.isalnum():
                messages.warning(request, "Password should be alphanumeric.")
                return redirect('change-password')
            else:
                user = request.user
                user.set_password(new1)
                user.save()
                update_session_auth_hash(request, user)

                messages.success(request, 'Password successfully changed.')
                return redirect('account')
        else:
            messages.warning(request, 'Wrong old password, please try again.')
            return redirect('change-password')
    return render(request, 'supplier/change_password.html', context=context)


'''
Create a new company
'''


def create_company(request, id):
    form = CreateCompany()
    user = User.objects.filter(id=id).first()
    user_type = user.user_type
    form.initial['company_name'] = user.company.name
    zimbabwean_towns = ['Select City ---', 'Beitbridge', 'Bindura', 'Bulawayo', 'Chinhoyi', 'Chirundu', 'Gweru',
                        'Harare', 'Hwange', 'Juliusdale', 'Kadoma', 'Kariba', 'Karoi', 'Kwekwe', 'Marondera',
                        'Masvingo', 'Mutare', 'Mutoko', 'Nyanga', 'Victoria Falls']

    if request.method == 'POST':
        form = CreateCompany(request.POST)
        if form.is_valid():
            if user_type == 'BUYER':
                company_name = request.POST.get('company_name')
                city = request.POST.get('city')
                street_number = request.POST.get('street_number')
                street_name = request.POST.get('street_name')
                address = street_number + street_name + city
                is_govnt_org = request.POST.get('is_govnt_org')
                logo = request.FILES.get('logo')
                company_name = user.company.name
                Company.objects.filter(name=company_name).update(contact_person=user.first_name, phone_number=user.phone_number, name=company_name, city=city, address=address, logo=logo,
                                                                 is_govnt_org=is_govnt_org)
                DeliveryBranch.objects.create(name='main branch', street_number=street_number, street_name=street_name,
                                                city=city, company=user.company, description='Main Branch')
                messages.success(request, 'Company registerd successfully.')
                return redirect('home')

            else:
                company_name = request.POST.get('company_name')
                street_number = request.POST.get('street_number')
                street_name = request.POST.get('street_name')
                city = request.POST.get('city')
                address = street_number + street_name + city
                logo = request.FILES.get('logo')
                iban_number = request.POST.get('iban_number')
                license_number = request.POST.get('license_number')
                new_company = Company.objects.filter(name=company_name).update(name=company_name, address=address,
                                                                               logo=logo, iban_number=iban_number,
                                                                               license_number=license_number)
                new_company.save()
                CompanyFuelUpdate.objects.create(company=new_company)
                return render(request, 'supplier/final_reg.html')

    return render(request, 'supplier/create_company.html',
                  {'form': form, 'user_type': user_type, 'zimbabwean_towns': zimbabwean_towns})


'''
Supplier Profile
'''


@login_required()
@user_role
def account(request):
    subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
    return render(request, 'supplier/user_profile.html', {'subsidiary': subsidiary})


'''
supplier activate whatsapp
'''


@login_required()
@user_role
def activate_whatsapp(request):
    user = User.objects.filter(id=request.user.id).first()
    if user.activated_for_whatsapp == False:
        user.activated_for_whatsapp = True
        user.save()
        messages.success(request, 'Your whatsApp has been activated successfully.')
        return redirect('fuel-request')

    else:
        user.activated_for_whatsapp = False
        user.save()
        messages.warning(request, 'Your whatsApp has been deactivated successfully.')
        return redirect('fuel-request')


'''
handling client applications
'''


@login_required
@user_role
def clients(request):
    clients = Account.objects.filter(supplier_company=request.user.company)
    return render(request, 'supplier/clients.html', {'clients': clients})


@login_required
def verify_client(request, id):
    user_permission(request)
    client = get_object_or_404(Account, id=id)
    if not client.is_verified:
        client.is_verified = True
        client.save()
        messages.success(request, f'{client.buyer_company.name.title()} successfully verified.')
        return redirect('supplier:clients')
    client.is_verified = False
    client.save()
    messages.success(request, f'{client.buyer_company.name.title()}"s verification overturned.')
    return redirect('supplier:clients')


@login_required
def view_client_id_document(request, id):
    user_permission(request)
    client = Account.objects.filter(id=id).first()
    if client:
        filename = client.id_document.name.split('/')[-1]
        response = HttpResponse(client.id_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        redirect('supplier:clients')
    return response


@login_required
def view_application_id_document(request, id):
    user_permission(request)
    client = Account.objects.filter(id=id).first()
    if client:
        filename = client.application_document.name.split('/')[-1]
        response = HttpResponse(client.application_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        redirect('supplier:clients')
    return response


@login_required
@user_role
def edit_delivery_schedule(request):
    if request.method == "POST":
        delivery_schedule = DeliverySchedule.objects.filter(id=int(request.POST['delivery_id'])).first()
        delivery_schedule.driver_name = request.POST['driver_name']
        delivery_schedule.phone_number = request.POST['phone_number']
        delivery_schedule.id_number = request.POST['id_number']
        delivery_schedule.vehicle_reg = request.POST['vehicle_reg']
        if request.POST['delivery_date']:
            if delivery_schedule.date_edit_count >= 3:
                messages.warning(request, "Sorry you have exceeded the number of permitted delivery date extensions,\
                                     you can not proceed.")
                return redirect('supplier:delivery_schedules')
            delivery_schedule.date = request.POST['delivery_date']
            delivery_schedule.date_edit_count += 1
        delivery_schedule.transport_company = request.POST['transport_company']
        delivery_schedule.save()

        action = "Updating Delivery Schedule"
        description = f"You have updated delivery schedule for buyer {delivery_schedule.transaction.buyer.company.name}"
        Activity.objects.create(company=delivery_schedule.transaction.buyer.company, user=request.user, action=action,
                                description=description, reference_id=delivery_schedule.id)
        messages.success(request, f"Schedule successfully updated.")
        return redirect('supplier:delivery_schedules')


'''
Fuel Requests
'''


@login_required()
@user_role
def fuel_request(request):
    notifications = Notification.objects.filter(action="new_request").filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(action="new_request").filter(is_read=False).count()
    sub = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
    requests = []
    complete_requests = []
    if sub.praz_reg_num != None:
        all_requests = FuelRequest.objects.filter(is_deleted=False, is_complete=False).all()
        for fuel_request in all_requests:
            if not fuel_request.is_direct_deal and not fuel_request.private_mode:
                requests.append(fuel_request)
            elif fuel_request.is_direct_deal and not fuel_request.private_mode:
                if fuel_request.last_deal == request.user.subsidiary_id:
                    requests.append(fuel_request)
                else:
                    pass
            elif not fuel_request.is_direct_deal and fuel_request.private_mode:
                account_exists = Account.objects.filter(supplier_company=request.user.company,
                                                        buyer_company=fuel_request.name.company).exists()
                if account_exists:
                    requests.append(fuel_request)
                else:
                    pass
            elif fuel_request.is_direct_deal and fuel_request.private_mode:
                if fuel_request.supplier_company == request.user.company:
                    requests.append(fuel_request)
                else:
                    pass
            else:
                pass
        requests.sort(key=attrgetter('date', 'time'), reverse=True)
    else:
        all_requests = FuelRequest.objects.filter(~Q(name__company__is_govnt_org=True)).filter(is_deleted=False,
                                                                                               wait=True,
                                                                                               is_complete=False).all()
        for fuel_request in all_requests:
            if not fuel_request.is_direct_deal and not fuel_request.private_mode:
                requests.append(fuel_request)
            elif fuel_request.is_direct_deal and not fuel_request.private_mode:
                if fuel_request.last_deal == request.user.subsidiary_id:
                    requests.append(fuel_request)
                else:
                    pass
            elif not fuel_request.is_direct_deal and fuel_request.private_mode:
                account_exists = Account.objects.filter(supplier_company=request.user.company,
                                                        buyer_company=fuel_request.name.company).exists()
                if account_exists:
                    requests.append(fuel_request)
                else:
                    pass
            elif fuel_request.is_direct_deal and fuel_request.private_mode:
                if fuel_request.supplier_company == request.user.company:
                    requests.append(fuel_request)
                else:
                    pass
            else:
                pass
        requests.sort(key=attrgetter('date', 'time'), reverse=True)

    for buyer_request in requests:
        if buyer_request.payment_method == 'USD':
            fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(
                payment_type='USD').first()
        elif buyer_request.payment_method == 'RTGS':
            fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(
                payment_type='RTGS').first()
        elif buyer_request.payment_method == 'USD & RTGS':
            fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(
                payment_type='USD & RTGS').first()
        else:
            fuel = None
        if buyer_request.dipping_stick_required == buyer_request.meter_required == buyer_request.pump_required == False:
            buyer_request.no_equipment = True
        if buyer_request.cash == buyer_request.ecocash == buyer_request.swipe == buyer_request.usd == False:
            buyer_request.no_payment = True
        # if not buyer_request.delivery_address.strip():
        #     buyer_request.delivery_address = f'N/A'
        if Offer.objects.filter(supplier_id=request.user, request_id=buyer_request).exists():
            offer = Offer.objects.filter(supplier_id=request.user, request_id=buyer_request).first()
            buyer_request.my_offer = f'{offer.quantity}ltrs @ ${offer.price}'
            buyer_request.offer_price = offer.price
            buyer_request.offer_quantity = offer.quantity
            buyer_request.offer_id = offer.id
            buyer_request.transport_fee = offer.transport_fee
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
        complete_requests = FuelRequest.objects.filter(is_complete=True).all()
        for buyer_request in complete_requests:
            if buyer_request.dipping_stick_required == buyer_request.meter_required == buyer_request.pump_required == False:
                buyer_request.no_equipment = True
    return render(request, 'supplier/fuel_request.html', {'notifications': notifications, 'num_of_notifications': num_of_notifications, 'requests': requests, 'complete_requests': complete_requests})


@login_required()
def new_fuel_request(request, id):
    user_permission(request)
    requests = FuelRequest.objects.filter(id=id, wait=True).all()
    return render(request, 'supplier/new_fuel_request.html', {'requests': requests})


'''
Fuel Stock operations
'''


@login_required
@user_role
def available_stock(request):
    updates = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).all()

    return render(request, 'supplier/available_fuel.html', {'updates': updates})


@login_required()
def stock_update(request, id):
    user_permission(request)
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
                    messages.warning(request, 'You can only reduce your petrol quantity.')
                    return redirect('available_stock')
                fuel_reduction = fuel_update.petrol_quantity - float(request.POST['quantity'])
                fuel_update.petrol_quantity = float(request.POST['quantity'])
                subsidiary_fuel.petrol_quantity = subsidiary_fuel.petrol_quantity - fuel_reduction
                subsidiary_fuel.save()

                stock_sord_update(request, request.user, fuel_reduction, 'Fuel Update', 'Petrol',
                                  fuel_update.payment_type)
                petrol_stock = fuel_update.petrol_quantity
                action = "Updating Fuel Stocks"
                description = f"You have updated petrol stock to {petrol_stock}L"
                Activity.objects.create(company=request.user.company, user=request.user, action=action,
                                        description=description, reference_id=fuel_update.id)

            else:
                if float(request.POST['quantity']) > available_diesel:
                    messages.warning(request, 'You can only reduce your diesel quantity.')
                    return redirect('available_stock')
                fuel_reduction = fuel_update.diesel_quantity - float(request.POST['quantity'])
                fuel_update.diesel_quantity = float(request.POST['quantity'])
                subsidiary_fuel.diesel_quantity = subsidiary_fuel.diesel_quantity - fuel_reduction
                subsidiary_fuel.save()

                stock_sord_update(request, request.user, fuel_reduction, 'Fuel Update', 'Diesel',
                                  fuel_update.payment_type)

                petrol_stock = fuel_update.diesel_quantity
                action = "Updating Fuel Stocks"
                description = f"You have updated diesel stock to {petrol_stock}L"
                Activity.objects.create(company=request.user.company, user=request.user, action=action,
                                        description=description, reference_id=fuel_update.id)

            fuel_update.cash = request.POST['cash']
            fuel_update.swipe = request.POST['swipe']
            if fuel_update.payment_type != 'USD':
                fuel_update.ecocash = request.POST['ecocash']
            fuel_update.save()

            messages.success(request, 'Fuel successfully updated.')
    return redirect('available_stock')


'''
Offers Operations
'''


@login_required()
@user_role
def my_offers(request):
    offers = Offer.objects.filter(supplier=request.user, is_accepted=False).all()
    for offer_temp in offers:
        if offer_temp.cash == offer_temp.ecocash == offer_temp.swipe == offer_temp.usd == False:
            offer_temp.no_payment = True
        if offer_temp.dipping_stick_available == offer_temp.meter_available == offer_temp.pump_available == False:
            offer_temp.no_equipments = True
        
    offers_pending = Offer.objects.filter(supplier=request.user, is_accepted=True).all()

    if request.method == 'POST':
        if request.POST.get('start_date') and request.POST.get('end_date') :
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()
            offers = Offer.objects.filter(supplier=request.user, is_accepted=False) \
            .filter(date__range=[start_date, end_date])
            
            for offer_temp in offers:
                if offer_temp.cash == offer_temp.ecocash == offer_temp.swipe == offer_temp.usd == False:
                    offer_temp.no_payment = True
                if offer_temp.dipping_stick_available == offer_temp.meter_available == offer_temp.pump_available == False:
                    offer_temp.no_equipments = True

            offers_pending = Offer.objects.filter(supplier=request.user, is_accepted=True) \
            .filter(date__range=[start_date, end_date])

            context = {
                'offers': offers,
                'offers_pending': offers_pending,
                'start_date':start_date,
                'end_date':end_date 
            }       
                
            return render(request, 'supplier/my_offers.html', context=context)

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
                offers = Offer.objects.filter(supplier=request.user, is_accepted=False) \
                .filter(date__range=[start_date, end_date])
                offers_pending = Offer.objects.filter(supplier=request.user, is_accepted=True) \
                .filter(date__range=[start_date, end_date])

            offers = offers.values('date', 'request__name__company__name, request__fuel_type','price', 'delivery_method', 'transport_fee', 'request__payment_method')  
            
            offers_pending = offers.values('date', 'request__name__company__name, request__fuel_type','price', 'delivery_method', 'transport_fee', 'request__payment_method')  

            fields = ['date', 'request__name__company__name, request__fuel_type','price', 'delivery_method', 'transport_fee', 'request__payment_method']

            df_offers = pd.DataFrame(offers, columns=fields)
            df_offers_pending = pd.DataFrame(offers_pending, columns=fields)

            df = df_offers.append(df_offers_pending)
            
            filename = f'{request.user.company.name}'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - Offers - {today}.csv'
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
                offers = Offer.objects.filter(supplier=request.user, is_accepted=False) \
                .filter(date__range=[start_date, end_date])
                offers_pending = Offer.objects.filter(supplier=request.user, is_accepted=True) \
                .filter(date__range=[start_date, end_date])

            context = {
                'offers': offers,
                'offers_pending':offers_pending,
                'date':today,
                'start_date':start_date,
                'end_date':end_date
            }  
                
            html_string = render_to_string('supplier/export/export_offers.html', context=context)
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} -Orders - {today}.pdf'
                return response        
    

    return render(request, 'supplier/my_offers.html', {'offers': offers, 'offers_pending': offers_pending})


@login_required()
def offer(request, id):
    user_permission(request)
    form = OfferForm(request.POST)
    if request.method == "POST":
        if float(request.POST.get('price')) != 0 and float(request.POST.get('quantity')) != 0:
            fuel_request = FuelRequest.objects.get(id=id)
            fuel_reserve = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id,
                                                                  payment_type='USD & RTGS').first()
            if fuel_request.payment_method == 'USD':
                fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id,
                                                              payment_type='USD').first()
            elif fuel_request.payment_method == 'RTGS':
                fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id,
                                                              payment_type='RTGS').first()
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
            offer_quantity = float(request.POST.get('quantity'))
            quantity = fuel_request.amount

            if offer_quantity <= available_fuel:
                if offer_quantity <= quantity:
                    offer = Offer()
                    offer.supplier = request.user
                    offer.request = fuel_request
                    offer.price = request.POST.get('price')
                    offer.transport_fee = request.POST.get('transport')
                    offer.quantity = request.POST.get('quantity')
                    offer.fuel_type = request.POST.get('fuel_type')
                    offer.usd = True if request.POST.get('usd') == "on" else False
                    offer.cash = True if request.POST.get('cash') == "on" else False
                    offer.ecocash = True if request.POST.get('ecocash') == "on" else False
                    offer.swipe = True if request.POST.get('swipe') == "on" else False
                    offer.delivery_method = fuel_request.delivery_method
                    if fuel_request.delivery_method.lower() == 'delivery':
                        pass
                    else:
                        offer.collection_address = request.POST.get('street_number') + " " + request.POST.get(
                            'street_name') + " " + request.POST.get('location')
                    offer.pump_available = True if request.POST.get('pump_available') == "on" else False
                    offer.dipping_stick_available = True if request.POST.get(
                        'dipping_stick_available') == "on" else False
                    offer.meter_available = True if request.POST.get('meter_available') == "on" else False
                    offer.save()

                    messages.success(request, 'Offer uploaded successfully.')

                    my_company = fuel_request.name.company
            
                    message = f'You have a new offer of {offer_quantity}L {fuel_request.fuel_type.lower()} at ${offer.price} from {request.user.company.name.title()}  for your request of {fuel_request.amount}L'
                    Notification.objects.create(handler_id=10, company=my_company, responsible_subsidiary=subsidiary, message=message, user=fuel_request.name, reference_id=offer.id,
                                                action="new_offer")
                    click_url = f'https://fuelfinderzim.com/new_fuel_offer/{offer.id}'
                    if offer.request.name.activated_for_whatsapp:
                        send_message(offer.request.name.phone_number,
                                     f'Your have received a new offer of {offer_quantity}L {fuel_request.fuel_type.lower()} at ${offer.price} from {request.user.company.name} {request.user.last_name} for your request of {fuel_request.amount}L click {click_url} to view details')
                    action = f"{request.user}  made an offer of {offer_quantity}L @ {request.POST.get('price')} to a request made by {fuel_request.name.username}"
                    service_station = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
                    reference = 'offers'
                    reference_id = offer.id
                    Audit_Trail.objects.create(company=request.user.company, service_station=service_station,
                                               user=request.user, action=action, reference=reference,
                                               reference_id=reference_id)

                    action = "Making Offer"
                    description = f"You have made an offer of {offer_quantity}L @ {request.POST.get('price')} to a request made by {fuel_request.name.company.name}"
                    Activity.objects.create(company=request.user.company, user=request.user, action=action,
                                            description=description, reference_id=offer.id)
                    return redirect('fuel-request')
                else:
                    messages.warning(request, 'You can not make an offer greater than the requested fuel quantity.')
                    return redirect('fuel-request')
            else:
                messages.warning(request, 'You can not offer fuel more than the available fuel stock.')
                return redirect('fuel-request')
        else:
            messages.warning(request, "Please provide a price to complete an offer.")
            return redirect('fuel-request')
    return render(request, 'supplier/fuel_request.html')


@login_required
def edit_offer(request, id):
    user_permission(request)
    offer = Offer.objects.get(id=id)
    fuel_reserve = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id,
                                                          payment_type='USD & RTGS').first()
    if request.method == 'POST':
        if offer.request.payment_method == 'USD':
            fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id,
                                                          payment_type='USD').first()
        elif offer.request.payment_method == 'RTGS':
            fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id,
                                                          payment_type='RTGS').first()
        subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()

        if offer.request.fuel_type.lower() == 'petrol':
            if fuel_reserve is not None:
                available_fuel = fuel.petrol_quantity + fuel_reserve.petrol_quantity
            else:
                available_fuel = fuel.petrol_quantity
        elif offer.request.fuel_type.lower() == 'diesel':
            if fuel_reserve is not None:
                available_fuel = fuel.diesel_quantity + fuel_reserve.diesel_quantity
            else:
                available_fuel = fuel.diesel_quantity
        new_offer = float(request.POST.get('quantity'))
        request_quantity = offer.request.amount
        if new_offer <= available_fuel:
            if new_offer <= request_quantity:
                offer.price = request.POST.get('price')
                offer.transport_fee = request.POST.get('transport')
                offer.quantity = request.POST.get('quantity')
                offer.usd = True if request.POST.get('usd') == "on" else False
                offer.cash = True if request.POST.get('cash') == "on" else False
                offer.ecocash = True if request.POST.get('ecocash') == "on" else False
                offer.swipe = True if request.POST.get('swipe') == "on" else False
                offer.delivery_method = offer.request.delivery_method
                if offer.request.delivery_method.lower() == 'delivery':
                    pass
                else:
                    offer.collection_address = request.POST.get('street_number') + " " + request.POST.get(
                        'street_name') + " " + request.POST.get('location')
                offer.pump_available = True if request.POST.get('pump_available') == "on" else False
                offer.dipping_stick_available = True if request.POST.get('dipping_stick_available') == "on" else False
                offer.meter_available = True if request.POST.get('meter_available') == "on" else False
                offer.save()
                messages.success(request, 'Offer successfully updated.')
                message = f'You have an updated offer of {new_offer}L {offer.request.fuel_type.lower()} at ${offer.price} from {request.user.company.name.title()} for your request of {offer.request.amount}L'
                Notification.objects.create(message=message, user=offer.request.name, reference_id=offer.id,
                                            action="new_offer")

                # action = "Updating Offer"
                # description = f"You have updated an offer of {new_offer}L {offer.request.fuel_type.lower()} at ${offer.price} from {request.user.company.name.title()} for your request of {offer.request.amount}L"
                # Activity.objects.create(company=request.user.company, user=request.user, action=action, description=description, reference_id=offer.id)
                return redirect('my_offers')
            else:
                messages.warning(request, 'You can not make an offer greater than the requested fuel quantity.')
                return redirect('my_offers')
        else:
            messages.warning(request, 'You can not offer fuel more than the available fuel stock')
            return redirect('my_offers')
    return render(request, 'supplier/fuel_request.html', {'offer': offer})


@login_required()
def accepted_offer(request, id):
    user_permission(request)
    transactions = Transaction.objects.filter(id=id).all()
    return render(request, 'supplier/new_transaction.html', {'transactions': transactions})


@login_required()
def rejected_offer(request, id):
    user_permission(request)
    offers = Offer.objects.filter(id=id).all()
    return render(request, 'supplier/my_offer.html', {'offers': offers})


'''
allocated quantities
'''


@login_required()
@user_role
def allocated_quantity(request):
    allocations = FuelAllocation.objects.filter(allocated_subsidiary_id=request.user.subsidiary_id).all()
    return render(request, 'supplier/allocated_quantity.html', {'allocations': allocations})


@login_required()
@user_role
def company(request):
    subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
    num_of_suppliers = User.objects.filter(subsidiary_id=request.user.subsidiary_id).count()
    return render(request, 'supplier/company.html', {'subsidiary': subsidiary, 'num_of_suppliers': num_of_suppliers})


'''
Transactions Operations
'''


@login_required
@user_role
def transaction(request):

    today = datetime.now().strftime("%m-%d-%y")
    transporters = Company.objects.filter(company_type="TRANSPORTER").all()
    trans = Transaction.objects.filter(supplier=request.user).all()
    
    for tran in trans:
        delivery_sched = DeliverySchedule.objects.filter(transaction=tran).first()
        if delivery_sched:
            tran.delivery_sched = delivery_sched
        tran.review = UserReview.objects.filter(transaction=tran).first()
        # if tran.is_complete == True:
        #     transactions.append(tran)
        # if tran.is_complete == False:
        #     transactions_pending.append(tran)
        
    transactions = trans.filter(is_complete=True)
    transactions_pending = trans.filter(is_complete=False) 


    context = {
        'transactions': transactions,
        'transactions_pending': transactions_pending,
        'transporters': transporters,
        'today': today
    }
    


    if request.method == "POST":
        if request.POST.get('transaction_id'):
            tran = Transaction.objects.get(id=request.POST.get('transaction_id'))
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
            return redirect('transaction')

        if request.POST.get('start_date') and request.POST.get('end_date') :
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()

            trans = Transaction.objects.filter(supplier=request.user).filter(date__range=[start_date, end_date])
    
            for tran in trans:
                delivery_sched = DeliverySchedule.objects.filter(transaction=tran).first()
                if delivery_sched:
                    tran.delivery_sched = delivery_sched
                tran.review = UserReview.objects.filter(transaction=tran).first()
              
            transactions = trans.filter(is_complete=True)
            transactions_pending = trans.filter(is_complete=False) 
                
        
            context = {
                'transactions': transactions.order_by('-date', '-time'),
                'transactions_pending': transactions_pending.order_by('-date', '-time'),
                'transporters': transporters,
                'today': today,
                'start_date': start_date,
                'end_date': end_date

            }


            return render(request, 'supplier/transactions.html', context=context)


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
                trans = Transaction.objects.filter(supplier=request.user).filter(date__range=[start_date, end_date])

            transactions = trans.filter(is_complete=True)
            transactions_pending = trans.filter(is_complete=False)  
            
            transactions = transactions.values('date','time', 'buyer__company__name',
             'offer__request__fuel_type', 'offer__request__amount', 'is_complete')
            transactions_pending =  transactions_pending.values('date','time', 'buyer__company__name',
             'offer__request__fuel_type', 'offer__request__amount', 'is_complete')
            fields = ['date','time', 'buyer__company__name', 'offer__request__fuel_type', 'offer__request__amount', 'is_complete']
            
            df_complete_trans = pd.DataFrame(transactions, columns=fields)
            df_in_complete_trans = pd.DataFrame(transactions_pending, columns=fields)

            df = df_complete_trans.append(df_in_complete_trans)

            # df = df[['date','noic_depot', 'fuel_type', 'quantity', 'currency', 'status']]
            filename = f'{request.user.company.name}'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - Transactions - {today}.csv'
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
                trans = Transaction.objects.filter(supplier=request.user).filter(date__range=[start_date, end_date])

            for tran in trans:
                delivery_sched = DeliverySchedule.objects.filter(transaction=tran).first()
                if delivery_sched:
                    tran.delivery_sched = delivery_sched
                tran.review = UserReview.objects.filter(transaction=tran).first()
                  
            transactions = trans.filter(is_complete=True)
            transactions_pending = trans.filter(is_complete=False) 
        
            context = {
                'transactions': transactions.order_by('-date', '-time'),
                'incomplete_transactions': transactions_pending.order_by('-date', '-time'),
                'date': today,
                'start_date': start_date,
                'end_date': end_date
            }

            html_string = render_to_string('supplier/export/export_transactions.html', context=context)
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} - Transactions - {today}.pdf'
                return response        
    

    return render(request, 'supplier/transactions.html', context=context)


@login_required
def complete_transaction(request, id):
    user_permission(request)
    transaction = Transaction.objects.filter(id=id).first()
    subsidiary_fuel = SubsidiaryFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).first()
    fuel_reserve = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id,
                                                          payment_type='USD & RTGS').first()
    if transaction.offer.request.payment_method == 'USD':
        fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id,
                                                      payment_type='USD').first()
        payment_type = 'USD'
    elif transaction.offer.request.payment_method == 'RTGS':
        fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id,
                                                      payment_type='RTGS').first()
        payment_type = 'RTGS'
    fuel_type = transaction.offer.request.fuel_type.lower()
    if fuel_type == 'petrol':
        if request.method == 'POST':
            # transaction_quantity = transaction.offer.quantity
            if transaction.offer.delivery_method == "DELIVERY":
                fuel_charge = float(request.POST['received']) - float(request.POST['transport_charge'])
                transaction_quantity = fuel_charge / float(transaction.offer.price)
            else:
                transaction_quantity = float(request.POST['received'])
            # transaction_quantity = int(float(request.POST['for_fuel']) / float(transaction.offer.price))
            if fuel_reserve is not None:
                available_fuel = fuel.petrol_quantity + fuel_reserve.petrol_quantity
            else:
                available_fuel = fuel.petrol_quantity
            if transaction_quantity <= available_fuel:

                transaction.proof_of_payment_approved = True
                transaction.paid += Decimal(request.POST['received'])
                transaction.paid_reserve = float(request.POST['received'])
                if transaction.offer.delivery_method == "DELIVERY":
                    transaction.fuel_money_reserve = float(request.POST['received']) - float(
                        request.POST['transport_charge'])
                else:
                    transaction.fuel_money_reserve = float(request.POST['received'])
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
                transaction_sord_update(request, user, transaction_quantity, 'SALE', 'Petrol', payment_type,
                                        transaction)

                # action = "Approving Payment"
                # description = f"You have approved payment for fuel from {transaction.buyer.company.name}"
                # Activity.objects.create(company=request.user.company, user=request.user, action=action,
                #                         description=description, reference_id=transaction.id)

                messages.success(request,
                                 "Proof of payment approved!, please create a delivery schedule for the buyer or upload a release note.")
                return redirect('transaction')
            else:
                messages.warning(request, "There is not enough petrol in stock to complete the transaction.")
                return redirect('transaction')
    elif fuel_type == 'diesel':
        if request.method == 'POST':
            # transaction_quantity = transaction.offer.quantity
            if transaction.offer.delivery_method == "DELIVERY":
                fuel_charge = float(request.POST['received']) - float(request.POST['transport_charge'])
                transaction_quantity = fuel_charge / float(transaction.offer.price)
            else:
                transaction_quantity = float(request.POST['received'])
            # transaction_quantity = int(float(request.POST['for_fuel']) / float(transaction.offer.price))
            if fuel_reserve is not None:
                available_fuel = fuel.diesel_quantity + fuel_reserve.diesel_quantity
            else:
                available_fuel = fuel.diesel_quantity
            if transaction_quantity <= available_fuel:

                transaction.proof_of_payment_approved = True
                transaction.paid += Decimal(request.POST['received'])
                transaction.paid_reserve = float(request.POST['received'])
                if transaction.offer.delivery_method == "DELIVERY":
                    transaction.fuel_money_reserve = float(request.POST['received']) - float(
                        request.POST['transport_charge'])
                else:
                    transaction.fuel_money_reserve = float(request.POST['received'])
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
                transaction_sord_update(request, user, transaction_quantity, 'SALE', 'Diesel', payment_type,
                                        transaction)

                # action = "Approving Payment"
                # description = f"You have approved payment for fuel from {transaction.buyer.company.name}"
                # Activity.objects.create(company=request.user.company, user=request.user, action=action,
                #                         description=description, reference_id=transaction.id)

                messages.success(request,
                                 "Proof of payment approved!, please create a delivery schedule for the buyer.")
                return redirect('transaction')
            else:
                messages.warning(request, "There is not enough diesel in stock to complete the transaction.")
                return redirect('transaction')
    return render(request, 'supplier/transactions.html')


def invoice(request, id):
    buyer = request.user
    transactions = Transaction.objects.filter(buyer=buyer, id=id).first()

    context = {
        'transactions': transactions
    }
    pdf = render_to_pdf('supplier/invoice.html', context)
    return HttpResponse(pdf, content_type='application/pdf')


@login_required()
def view_invoice(request, id):
    user_permission(request)
    transaction = Transaction.objects.filter(supplier=request.user, id=id).all()
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
    return render(request, 'supplier/invoice2.html', context)


def download_proof(request, id):
    document = Transaction.objects.filter(id=id).first()
    if document:
        filename = document.proof_of_payment.name.split('/')[-1]
        response = HttpResponse(document.proof_of_payment, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect('transaction')
    return response


@login_required
def client_transaction_history(request, id):
    user_permission(request)
    client = Account.objects.filter(id=id).first()

    contribution = get_customer_contributions(request.user.id, client.buyer_company)
    cash_contribution = get_customer_contributions(request.user.id, client.buyer_company)[1]
    total_cash = client_revenue(request.user.id, client.buyer_company)
    all_requests, todays_requests = total_requests(client.buyer_company)

    trns = Transaction.objects.filter(supplier=request.user, buyer__company=client.buyer_company)
    transactions = []
    for tran in trns:
        tran.revenue = float(tran.offer.request.amount) * float(tran.offer.price)
        transactions.append(tran)

    return render(request, 'supplier/client_activity.html', {'transactions': transactions, 'client': client,
                                                             'contribution': contribution,
                                                             'cash_contribution': cash_contribution,
                                                             'total_cash': total_cash,
                                                             'all_requests': all_requests,
                                                             'todays_requests': todays_requests})


@login_required()
def stock_sord_update(request, user, quantity, action, fuel_type, payment_type):
    user_permission(request)
    initial_sord = SordSubsidiaryAuditTrail.objects.filter(subsidiary__id=request.user.subsidiary_id,
                                                           fuel_type=fuel_type, payment_type=payment_type).all()
    sord_quantity = []
    for sord in initial_sord:
        if sord.end_quantity != 0:
            sord_quantity.append(sord)
        else:
            pass
    sord_quantity.sort(key=attrgetter('last_updated'), reverse=True)
    balance_brought_forward = quantity
    for entry in sord_quantity:
        if balance_brought_forward != 0:
            subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
            if entry.end_quantity < balance_brought_forward:
                SordSubsidiaryAuditTrail.objects.create(sord_no=entry.sord_no, action_no=entry.action_no + 1,
                                                        action=action, initial_quantity=entry.end_quantity,
                                                        quantity_sold=entry.end_quantity, end_quantity=0,
                                                        received_by=user, fuel_type=entry.fuel_type,
                                                        subsidiary=subsidiary, payment_type=payment_type)
                sord_obj = SordCompanyAuditTrail.objects.filter(sord_no=entry.sord_no).first()
                sord_obj2 = SordActionsAuditTrail.objects.filter(sord_num=entry.sord_no).first()
                SordActionsAuditTrail.objects.create(sord_num=sord_obj.sord_no,
                                                     action_num=sord_obj.action_no + 1,
                                                     allocated_quantity=entry.end_quantity,
                                                     action_type="Stock Update",
                                                     supplied_from=subsidiary.name,
                                                     price=sord_obj2.price,
                                                     allocated_by=request.user.username,
                                                     allocated_to=user.company.name,
                                                     fuel_type=entry.fuel_type,
                                                     payment_type=payment_type)
                sord_obj.action_no += 1
                sord_obj.save()

                balance_brought_forward = balance_brought_forward - entry.end_quantity
            else:
                SordSubsidiaryAuditTrail.objects.create(sord_no=entry.sord_no, action_no=entry.action_no + 1,
                                                        action=action, initial_quantity=entry.end_quantity,
                                                        quantity_sold=balance_brought_forward,
                                                        end_quantity=entry.end_quantity - balance_brought_forward,
                                                        received_by=user, fuel_type=entry.fuel_type,
                                                        subsidiary=subsidiary, payment_type=payment_type)
                sord_obj = SordCompanyAuditTrail.objects.filter(sord_no=entry.sord_no).first()
                sord_obj2 = SordActionsAuditTrail.objects.filter(sord_num=entry.sord_no).first()
                SordActionsAuditTrail.objects.create(sord_num=sord_obj.sord_no,
                                                     action_num=sord_obj.action_no + 1,
                                                     allocated_quantity=balance_brought_forward,
                                                     action_type="Stock Update",
                                                     supplied_from=subsidiary.name,
                                                     price=sord_obj2.price,
                                                     allocated_by=request.user.username,
                                                     allocated_to=user.company.name,
                                                     fuel_type=entry.fuel_type,
                                                     payment_type=payment_type)
                sord_obj.action_no += 1
                sord_obj.save()
                balance_brought_forward = 0


@login_required()
def transaction_sord_update(request, user, quantity, action, fuel_type, payment_type, transaction):
    user_permission(request)
    initial_sord = SordSubsidiaryAuditTrail.objects.filter(subsidiary__id=request.user.subsidiary_id,
                                                           fuel_type=fuel_type, payment_type=payment_type).all()
    sord_quantity = []
    account_sord_list = []
    for sord in initial_sord:
        if sord.end_quantity != 0:
            sord_quantity.append(sord)
        else:
            pass
    sord_quantity.sort(key=attrgetter('last_updated'), reverse=True)
    balance_brought_forward = quantity
    for entry in sord_quantity:
        if balance_brought_forward != 0:
            subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
            if entry.end_quantity < balance_brought_forward:
                SordSubsidiaryAuditTrail.objects.create(sord_no=entry.sord_no, action_no=entry.action_no + 1,
                                                        action=action, initial_quantity=entry.end_quantity,
                                                        quantity_sold=entry.end_quantity, end_quantity=0,
                                                        received_by=user, fuel_type=entry.fuel_type,
                                                        subsidiary=subsidiary, payment_type=payment_type)

                sord_obj = SordCompanyAuditTrail.objects.filter(sord_no=entry.sord_no).first()
                sord_obj2 = SordActionsAuditTrail.objects.filter(sord_num=entry.sord_no).first()
                SordActionsAuditTrail.objects.create(sord_num=sord_obj.sord_no,
                                                     action_num=sord_obj.action_no + 1,
                                                     allocated_quantity=entry.end_quantity,
                                                     action_type="Sale",
                                                     supplied_from=subsidiary.name,
                                                     price=sord_obj2.price,
                                                     allocated_by=request.user.username,
                                                     allocated_to=user.company.name,
                                                     fuel_type=entry.fuel_type,
                                                     payment_type=payment_type)
                sord_obj.action_no += 1
                sord_obj.save()

                balance_brought_forward = balance_brought_forward - entry.end_quantity
                account_sord_list.append(entry.sord_no)
            else:
                SordSubsidiaryAuditTrail.objects.create(sord_no=entry.sord_no, action_no=entry.action_no + 1,
                                                        action=action, initial_quantity=entry.end_quantity,
                                                        quantity_sold=balance_brought_forward,
                                                        end_quantity=entry.end_quantity - balance_brought_forward,
                                                        received_by=user, fuel_type=entry.fuel_type,
                                                        subsidiary=subsidiary, payment_type=payment_type)

                sord_obj = SordCompanyAuditTrail.objects.filter(sord_no=entry.sord_no).first()
                sord_obj2 = SordActionsAuditTrail.objects.filter(sord_num=entry.sord_no).first()
                SordActionsAuditTrail.objects.create(sord_num=sord_obj.sord_no,
                                                     action_num=sord_obj.action_no + 1,
                                                     allocated_quantity=balance_brought_forward,
                                                     action_type="Sale",
                                                     supplied_from=subsidiary.name,
                                                     price=sord_obj2.price,
                                                     allocated_by=request.user.username,
                                                     allocated_to=user.company.name,
                                                     fuel_type=entry.fuel_type,
                                                     payment_type=payment_type)
                sord_obj.action_no += 1
                sord_obj.save()

                balance_brought_forward = 0
                account_sord_list.append(entry.sord_no)
    account = AccountHistory.objects.filter(transaction=transaction, sord_number=None).first()
    account.sord_number = ','.join(map(str, account_sord_list))
    account.save()


'''
Delivery Schedule Operations
'''


@login_required
def create_delivery_schedule(request):
    user_permission(request)
    if request.method == 'POST':
        schedule = DeliverySchedule.objects.create(
            date=request.POST['delivery_date'],
            transaction=Transaction.objects.filter(id=int(request.POST['transaction'])).first(),
            driver_name=request.POST['driver_name'],
            phone_number=request.POST['phone_number'],
            id_number=request.POST['id_num'],
            transport_company=request.POST['transport_company'],
            vehicle_reg=request.POST['vehicle_reg'],
            delivery_time=request.POST['delivery_time']
        )
        transaction = Transaction.objects.filter(id=int(request.POST['transaction'])).first()
        transaction.proof_of_payment = None
        transaction.pending_proof_of_payment = False
        transaction.save()
        schedule.delivery_quantity = int(float(transaction.fuel_money_reserve) / float(transaction.offer.price))
        schedule.amount_for_fuel = transaction.fuel_money_reserve
        schedule.save()
        payment_history = AccountHistory.objects.filter(transaction=transaction, value=0.00).first()
        payment_history.value += transaction.paid_reserve
        payment_history.balance -= transaction.paid_reserve
        payment_history.delivery_schedule = schedule
        payment_history.save()

        action = "Creating Delivery Schedule"
        description = f"You have created delivery schedule for {transaction.buyer.company.name}"
        Activity.objects.create(company=request.user.company, user=request.user, action=action, description=description,
                                reference_id=schedule.id)
        messages.success(request, "Schedule successfully created.")
        message = f"{schedule.transaction.supplier.company} has created a delivery schedule for you, click to view schedule"
        Notification.objects.create(user=schedule.transaction.buyer, action='schedule', message=message,
                                    reference_id=schedule.id)

        return redirect('transaction')


@login_required
def delivery_schedules(request):
    user_permission(request)
    schedules = DeliverySchedule.objects.filter(transaction__supplier=request.user).all()
    
    for schedule in schedules:
        if schedule.transaction.offer.delivery_method.lower() == 'delivery':
            schedule.delivery_address = schedule.transaction.offer.request.delivery_address
        else:
            schedule.delivery_address = schedule.transaction.offer.collection_address

    completed_schedules = schedules.filter(confirmation_date__isnull=False)
    pending_schedules = schedules.filter(confirmation_date__isnull=True)        
        
    if request.method == 'POST':
        if request.FILES.get('supplier_document') and request.POST.get('delivery_id'):
            supplier_document = request.FILES.get('supplier_document')
            delivery_id = request.POST.get('delivery_id')
            schedule = DeliverySchedule.objects.get(id=delivery_id)
            schedule.supplier_document = supplier_document
            schedule.save()
            messages.success(request, "File Successfully Uploaded.")
            msg = f"Delivery confirmed for {schedule.transaction.buyer.company}, click to view confirmation document"
            # Notification.objects.create(user=request.user, action='DELIVERY', message=msg, reference_id=schedule.id)
            return redirect('supplier:delivery_schedules')

        if request.POST.get('start_date') and request.POST.get('end_date') :
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()
            schedules = DeliverySchedule.objects.filter(transaction__supplier__company=request.user.company).filter(date__range=[start_date, end_date])
            
            for schedule in schedules:
                schedule.depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                if schedule.transaction.offer.delivery_method.lower() == 'delivery':
                    schedule.delivery_address = schedule.transaction.offer.request.delivery_address
                else:
                    schedule.delivery_address = schedule.transaction.offer.collection_address

            completed_schedules = schedules.filter(confirmation_date__isnull=False)
            pending_schedules = schedules.filter(confirmation_date__isnull=True)  

            context = {
                'pending_schedules': pending_schedules,
                'completed_schedules': completed_schedules,
                'start_date':start_date,
                'end_date':end_date 
            }       
                
            return render(request, 'supplier/delivery_schedules.html', context=context)

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
                schedules = DeliverySchedule.objects.filter(transaction__supplier__company=request.user.company).filter(date__range=[start_date, end_date])

                for schedule in schedules:
                    schedule.depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                    if schedule.transaction.offer.delivery_method.lower() == 'delivery':
                        schedule.delivery_address = schedule.transaction.offer.request.delivery_address
                    else:
                        schedule.delivery_address = schedule.transaction.offer.collection_address

            completed_schedules = schedules.filter(confirmation_date__isnull=False)
            pending_schedules = schedules.filter(confirmation_date__isnull=True) 

            completed_schedules = completed_schedules.values('date','transaction','driver_name', 'phone_number',
            'id_number','vehicle_reg', 'delivery_time')
            pending_schedules = pending_schedules.values('date','transaction','driver_name', 'phone_number',
            'id_number','vehicle_reg', 'delivery_time')  
        
            fields = ['date','transaction','driver_name', 'phone_number','id_number','vehicle_reg', 'delivery_time']

            df_completed_schedules = pd.DataFrame(completed_schedules, columns=fields)
            df_pending_schedules = pd.DataFrame(pending_schedules, columns=fields)

            df = df_completed_schedules.append(df_pending_schedules)
            
            filename = f'{request.user.company.name}'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - {today}.csv'
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
                schedules = DeliverySchedule.objects.filter(transaction__supplier__company=request.user.company).filter(date__range=[start_date, end_date])

                for schedule in schedules:
                    schedule.depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                    if schedule.transaction.offer.delivery_method.lower() == 'delivery':
                        schedule.delivery_address = schedule.transaction.offer.request.delivery_address
                    else:
                        schedule.delivery_address = schedule.transaction.offer.collection_address

                completed_schedules = schedules.filter(confirmation_date__isnull=False)
                pending_schedules = schedules.filter(confirmation_date__isnull=True)

            context = {
                'completed_schedules': completed_schedules,
                'pending_schedules':pending_schedules,
                'date':today,
                'start_date':start_date,
                'end_date':end_date
            }  
                
            html_string = render_to_string('supplier/export/export_delivery_schedules.html', context=context)
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} -Orders - {today}.pdf'
                return response        
        


    return render(request, 'supplier/delivery_schedules.html', {'pending_schedules': pending_schedules, 'completed_schedules': completed_schedules})


@login_required()
def view_delivery_schedule(request, id):
    user_permission(request)
    if request.method == 'POST':
        supplier_document = request.FILES.get('supplier_document')
        delivery_id = request.POST.get('delivery_id')
        schedule = get_object_or_404(DeliverySchedule, id=delivery_id)
        schedule.supplier_document = supplier_document
        schedule.save()
        messages.success(request, "File Successfully Uploaded.")
        msg = f"Delivery Confirmed for {schedule.transaction.buyer.company}, Click To View Confirmation Document"
        Notification.objects.create(user=request.user, action='DELIVERY', message=msg, reference_id=schedule.id)
        return redirect('delivery_schedules')
    schedule = DeliverySchedule.objects.filter(id=id).first()
    if schedule.transaction.offer.delivery_method.lower() == 'delivery':
        schedule.delivery_address = schedule.transaction.offer.request.delivery_address
    else:
        schedule.delivery_address = schedule.transaction.offer.collection_address
    return render(request, 'supplier/view_delivery_schedule.html', {'schedule': schedule})


@login_required()
def view_confirmation_doc(request, id):
    user_permission(request)
    payment = AccountHistory.objects.filter(delivery_schedule__id=id).first()
    payment.quantity = float(payment.value) / float(payment.transaction.offer.price)
    context = {
        'payment': payment
    }
    return render(request, 'supplier/delivery_note.html', context=context)


@login_required()
def view_delivery_note(request, id):
    user_permission(request)
    delivery = AccountHistory.objects.filter(id=id).first()
    if delivery:
        filename = delivery.delivery_note.name.split('/')[-1]
        response = HttpResponse(delivery.delivery_note, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        redirect('transactions')
    return response


@login_required()
def upload_release_note(request, id):
    user_permission(request)
    payment_history = AccountHistory.objects.filter(id=id).first()
    transaction = Transaction.objects.filter(id=payment_history.transaction.id).first()
    if request.method == 'POST':
        transaction.release_date = request.POST['release_date']

        transaction.proof_of_payment = None
        transaction.pending_proof_of_payment = False
        transaction.save()
        payment_history.value += transaction.paid_reserve
        payment_history.balance -= transaction.paid_reserve
        payment_history.release_date = request.POST['release_date']
        payment_history.release_activated = True
        payment_history.save()

        action = "Creating Release Note"
        description = f"You have created release note for {transaction.buyer.company.name}"
        Activity.objects.create(company=request.user.company, user=request.user, action=action, description=description,
                                reference_id=payment_history.id)
        messages.success(request, "Release note successfully created.")
        return redirect(f'/supplier/payment-and-release-notes/{transaction.id}')


@login_required()
def edit_release_note(request, id):
    user_permission(request)
    release = AccountHistory.objects.filter(id=id).first()
    if request.method == 'POST':
        release.release_date = request.POST['release_date']
        release.release_activated = True
        release.save()
        action = "Updating Release Note"
        description = f"You have updated release note for {release.transaction.buyer.company.name}"
        Activity.objects.create(company=request.user.company, user=request.user, action=action, description=description,
                                reference_id=release.transaction.id)
        return redirect(f'/supplier/payment-and-release-notes/{release.transaction.id}')


@login_required()
def payment_release_notes(request, id):
    user_permission(request)
    transaction = Transaction.objects.filter(id=id).first()
    payment_history = AccountHistory.objects.filter(transaction=transaction).all()
    return render(request, 'supplier/payment_and_rnote.html', {'payment_history': payment_history})


@login_required()
def view_supplier_doc(request, id):
    user_permission(request)
    delivery = DeliverySchedule.objects.filter(id=id).first()
    if delivery:
        filename = delivery.supplier_document.name.split('/')[-1]
        response = HttpResponse(delivery.supplier_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        redirect('supplier:delivery_schedules')
    return response


@login_required()
def del_supplier_doc(request, id):
    user_permission(request)
    delivery = DeliverySchedule.objects.filter(id=id).first()
    delivery.supplier_document = None
    delivery.save()
    messages.success(request, 'Document removed successfully,')
    return redirect('supplier:delivery_schedules')


@login_required()
def supplier_release_note(request, id):
    user_permission(request)
    transaction = Transaction.objects.filter(id=id).first()
    if request.method == 'POST':
        transaction.release_date = request.POST['release_date']

        transaction.proof_of_payment = None
        transaction.pending_proof_of_payment = False
        transaction.save()
        payment_history = AccountHistory.objects.filter(transaction=transaction, value=0.00).first()
        payment_history.value += transaction.paid_reserve
        payment_history.balance -= transaction.paid_reserve
        payment_history.release_note = request.FILES.get('release_note')
        payment_history.release_activated = True
        payment_history.save()

        action = "Creating Release Note"
        description = f"You have created release note for {transaction.buyer.company.name}"
        Activity.objects.create(company=request.user.company, user=request.user, action=action, description=description,
                                reference_id=payment_history.id)
        messages.success(request, "Release note successfully uploaded.")
        return redirect(f'/supplier/payment-and-release-notes/{id}')


"""

payment history

"""


@login_required()
def payment_history(request, id):
    user_permission(request)
    transaction = Transaction.objects.filter(id=id).first()
    payment_history = AccountHistory.objects.filter(transaction=transaction).all()
    return render(request, 'supplier/payment_history.html', {'payment_history': payment_history})


@login_required()
def mark_completion(request, id):
    user_permission(request)
    transaction = Transaction.objects.filter(id=id).first()
    transaction.is_complete = True
    transaction.save()

    messages.success(request, 'Transaction is now complete.')
    return redirect('transaction')


@login_required()
def view_release_note(request, id):
    user_permission(request)
    payment = AccountHistory.objects.filter(id=id).first()
    payment.quantity = float(payment.value) / float(payment.transaction.offer.price)
    context = {
        'payment': payment
    }
    return render(request, 'supplier/release_note.html', context=context)


@login_required()
def download_release_note(request, id):
    user_permission(request)
    payment = AccountHistory.objects.filter(id=id).first()
    payment.quantity = float(payment.value) / float(payment.transaction.offer.price)
    context = {
        'payment': payment
    }
    return render(request, 'supplier/r_note.html', context=context)


@login_required()
@user_role
def activity(request):
    filtered_activities = None
    activities = Activity.objects.exclude(date=today).filter(user=request.user)
    for activity in activities:
        if activity.action == 'Making Offer':
            activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()
        elif activity.action == 'Updating Fuel Stocks':
            activity.fuel_object = SuballocationFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.action == 'Creating Delivery Schedule':
            activity.delivery = DeliverySchedule.objects.filter(id=activity.reference_id).first()
            activity.subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
        elif activity.action == 'Updating Delivery Schedule':
            activity.delivery = DeliverySchedule.objects.filter(id=activity.reference_id).first()
            activity.subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
        
    current_activities = Activity.objects.filter(user=request.user, date=today).all()
    for activity in current_activities:
        if activity.action == 'Making Offer':
            activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()
        elif activity.action == 'Updating Fuel Stocks':
            activity.fuel_object = SuballocationFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.action == 'Creating Delivery Schedule':
            activity.delivery = DeliverySchedule.objects.filter(id=activity.reference_id).first()
            activity.subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
        elif activity.action == 'Updating Delivery Schedule':
            activity.delivery = DeliverySchedule.objects.filter(id=activity.reference_id).first()
            activity.subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
    depot = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()

    if request.method == "POST":
        if request.POST.get('start_date') and request.POST.get('end_date') :
            filtered = True;
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()
            
            filtered_activities = Activity.objects.filter(user=request.user).filter(date__range=[start_date, end_date])
            
            for activity in filtered_activities:
                if activity.action == 'Making Offer':
                    activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()
                elif activity.action == 'Updating Fuel Stocks':
                    activity.fuel_object = SuballocationFuelUpdate.objects.filter(id=activity.reference_id).first()
                elif activity.action == 'Creating Delivery Schedule':
                    activity.delivery = DeliverySchedule.objects.filter(id=activity.reference_id).first()
                    activity.subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
                elif activity.action == 'Updating Delivery Schedule':
                    activity.delivery = DeliverySchedule.objects.filter(id=activity.reference_id).first()
                    activity.subsidiary = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()

            depot = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()

            context = {
                'filtered_activities': filtered_activities,
                'start_date': start_date,
                'end_date': end_date,
                'depot': depot,
            }

            return render(request, 'supplier/activity.html', context=context)

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
                filtered_activities = Activity.objects.filter(user=request.user).filter(date__range=[start_date, end_date])
                      
            fields = ['date','time', 'company__name', 'action', 'description', 'reference_id']
            
            if filtered_activities:
                filtered_activities = filtered_activities.values('date','time', 'company__name', 'action', 'description', 'reference_id')
                df = pd.DataFrame(filtered_activities, columns=fields)
            else:
                df_current = pd.DataFrame(current_activities.values('date','time', 'company__name', 'action', 'description', 'reference_id'), columns=fields)
                df_previous = pd.DataFrame(activities.values('date','time', 'company__name', 'action', 'description', 'reference_id'), columns=fields)
                df = df_current.append(df_previous)

            filename = f'{request.user.company.name}'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - Activity - {today}.csv'
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
                filtered_activities = Activity.objects.filter(user=request.user).filter(date__range=[start_date, end_date])

            context = {
                'filtered_activities': filtered_activities,
                'start_date':start_date,
                'current_activities': current_activities,
                'activities':activities, 'end_date':end_date,
                'date':today
            }

            html_string = render_to_string('supplier/export/export_activities.html', context=context)
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} - Activities - {today}.pdf'
                return response

    return render(request, 'supplier/activity.html', {'activities': activities, 'depot': depot, 'current_activities': current_activities})


@login_required()
def hq_notifier(request, id):
    user_permission(request)
    depot = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
    if id == 1:
        message = 'Requesting for more USD fuel'
        Notification.objects.create(handler_id=7, message=message, reference_id=id, responsible_subsidiary=depot, action="FOR_FUEL")
    elif id == 2:
        message = 'Requesting for more RTGS fuel'
        Notification.objects.create(handler_id=7, message=message, reference_id=id, responsible_subsidiary=depot, action="FOR_FUEL")
    else:
        message = 'Requesting for more USD & RTGS fuel'
        Notification.objects.create(handler_id=7, message=message, reference_id=id, responsible_subsidiary=depot, action="FOR_FUEL")
    messages.success(request, "Request for more fuel made successfully.")
    return redirect('supplier:available_stock')


def notication_handler(request, id):
    my_handler = id
    if my_handler == 15:
        notifications = Notification.objects.filter(handler_id=my_handler).all()
        for notification in notifications:
            notification.is_read = True
            notification.save()
        return redirect('fuel-request')
    else:
        notifications = Notification.objects.filter(handler_id=my_handler).all()
        for notification in notifications:
            notification.is_read = True
            notification.save()
        return redirect('fuel-request')

def notication_reader(request):
    notifications = Notification.objects.filter(action="new_request").filter(is_read=False).all()
    for notification in notifications:
        notification.is_read = True
        notification.save()
    return redirect('fuel-request')