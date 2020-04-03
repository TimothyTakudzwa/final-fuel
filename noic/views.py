import secrets
from validate_email import validate_email
# from datetime import datetime, timedelta, date
import datetime

from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, update_session_auth_hash, login, logout
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from itertools import chain
from operator import attrgetter

from buyer.models import User, FuelRequest
from users.forms import DepotContactForm
from company.models import Company, CompanyFuelUpdate
from supplier.models import Subsidiaries, SubsidiaryFuelUpdate, FuelAllocation, Transaction, Offer, DeliverySchedule
from fuelUpdates.models import SordCompanyAuditTrail
from users.models import SordActionsAuditTrail, Activity
from accounts.models import AccountHistory
from users.views import message_is_sent
from fuelfinder.helper_functions import random_password
from national.models import Order, NationalFuelUpdate, SordNationalAuditTrail, DepotFuelUpdate, NoicDepot

from .lib import *
from zeraPortal.lib import *

user = get_user_model()

# Create your views here.
@login_required()
def orders(request):
    orders = Order.objects.all()
    form1 = DepotContactForm()
    depots = NoicDepot.objects.all()
    form1.fields['depot'].choices = [((depot.id, depot.name)) for depot in depots]
    for order in orders:
        order.allocation = SordNationalAuditTrail.objects.filter(order=order).first()

    return render(request, 'noic/orders.html', {'orders': orders, 'form1': form1})


@login_required()
def activity(request):
    activities = Activity.objects.filter(user=request.user).all()
    return render(request, 'noic/activity.html', {'activities': activities})


@login_required()
def dashboard(request):
    capacities = NationalFuelUpdate.objects.all()
    depots = DepotFuelUpdate.objects.all()
    noic_usd_diesel = 0
    noic_rtgs_diesel = 0
    noic_usd_petrol = 0
    noic_rtgs_petrol = 0
    for depot in depots:
        noic_usd_diesel += depot.usd_diesel
        noic_rtgs_diesel += depot.rtgs_diesel
        noic_usd_petrol += depot.usd_petrol
        noic_rtgs_petrol += depot.rtgs_petrol

    return render(request, 'noic/dashboard.html', {'capacities': capacities, 'depots': depots, 'noic_usd_diesel':noic_usd_diesel, 'noic_rtgs_diesel': noic_rtgs_diesel, 'noic_usd_petrol': noic_usd_petrol, 'noic_rtgs_petrol': noic_rtgs_petrol})


@login_required()
def allocations(request):
    allocations = SordNationalAuditTrail.objects.all()
    return render(request, 'noic/allocations.html', {'allocations': allocations})


@login_required()
def depots(request):
    global depot
    depots = NoicDepot.objects.all()
    form1 = DepotContactForm()
    zimbabwean_towns = ['Select City ---', 'Beitbridge', 'Bindura', 'Bulawayo', 'Chinhoyi', 'Chirundu', 'Gweru',
                        'Harare','Hwange', 'Juliusdale', 'Kadoma', 'Kariba', 'Karoi', 'Kwekwe', 'Marondera', 'Masvingo',
                        'Mutare', 'Mutoko', 'Nyanga', 'Victoria Falls']
    Harare = ['Arcadia', 'Ardbennie', 'Ashdown Park', 'Avenues', 'Avondale', 'Avonlea', 'Belgravia', 'Belvedere',
              'Bluff Hill', 'Borrowdale', 'Borrowdale', 'Braeside', 'Budiriro', 'CBD', 'Chisipiti', 'Cranbourne',
              'Dzivaresekwa', 'Eastlea', 'Emerald Hill', 'Epworth', 'Glen Lorne', 'Glen Norah', 'Glen View',
              'Graniteside', 'Greencroft', 'Greendale', 'Greystone Park', 'Gun Hill', 'Hatcliffe', 'Helensvale',
              'HighfieldKambuzuma', 'Highlands', 'Hillside', 'Houghton Park', 'Kuwadzana', 'Mabelreign', 'Mabvuku',
              'Mandara', 'Manresa', 'Marimba Park', 'Marlborough', 'Mbare', 'Meyrick Park', 'Milton Park',
              'Mount Pleasant', 'Msasa', 'Mufakose', 'Newlands', 'Pomona', 'Prospect', 'Queensdale', 'Southerton',
              'Southerton', 'Sunningdale', 'Tafara', 'The Grange', 'Tynwald', 'Vainona', 'Warren Park', 'Warren Park']
    Bulawayo = ['Ascot', 'Barbour Fields', 'Barham Green', 'Beacon Hill', 'Bellevue', 'Belmont',
                'Belmont Industrial area', 'Bradfield', 'New Luveve', 'Newsmansford', 'Newton', 'Newton West',
                'Nguboyenja', 'Njube', 'Nketa', 'Nkulumane', 'North End', 'North Lynne', 'North Trenance', 'Northlea',
                'Northvale', 'Ntaba Moyo']
    Mutare = ['Avenues', 'Bordervale', 'Chikanga', 'Dangamvura', 'Darlington', 'Fairbridge Park', 'Fern Valley',
              'Florida', 'Garikai', 'Gimboki', 'Greenside Extension', 'Greeside', 'Hillside', 'Mai Maria',
              'Morningside', 'Murambi', 'Musha Mukadzi', 'Natview Park', 'Palmerstone', 'Sakubva', 'Tigers Kloof',
              'Toronto', 'Utopia', 'Weirmouth', 'Westlea', 'Yeovil']
    Gweru = ['Ascot', 'Athlone', 'Bata', 'Bristle', 'Clydesdale Park', 'Daylesford', 'Gweru East', 'Haben Park',
             'Hertifordshire', 'Ivene', 'Kopje', 'Lundi Park', 'Mkoba', 'Montrose', 'Mtausi Park', 'Nashville',
             'Nehosho', 'Ridgemont', 'Riverside', 'Senga', 'Southdowns', 'Southview', 'ThornHill Air FieldGreen Dale',
             'Windsor Park', 'Woodlands Park']

    if request.method == 'POST':
        # check if email exists
        if User.objects.filter(email=request.POST.get('email')).exists():
            messages.warning(request, 'Invalid Email')
            return redirect('noic:depots')

        name = request.POST['name']
        city = request.POST['city']
        location = request.POST['location']
        destination_bank = request.POST['destination_bank']
        account_number = request.POST['account_number']
        praz_reg_num = request.POST['praz']
        vat = request.POST['vat']
        opening_time = request.POST['opening_time']
        closing_time = request.POST['closing_time']
        license_num = request.POST['licence']
        depot = NoicDepot.objects.create(is_active=True, license_num=license_num, praz_reg_num=praz_reg_num,
                                                 vat=vat, account_number=account_number,
                                                 destination_bank=destination_bank, city=city, address=location,
                                                name=name,
                                                 opening_time=opening_time, closing_time=closing_time)
        depot.save()

        depot_id = depot.id
        
        fuel_update = DepotFuelUpdate.objects.create(depot=depot)
        fuel_update.save()

        action = "Depot Creation"
        description = f"You have created another NOIC Depot {depot.name}"
        Activity.objects.create(depot=depot, user=request.user,
                                    action=action, description=description, reference_id=depot.id)
        messages.success(request, 'Depot Created Successfully')
        
        depots = NoicDepot.objects.all()
        
        return render(request, 'noic/depots.html',
                  {'depots': depots, 'form1': form1, 'add_user' : 'show', 'Harare': Harare, 'Bulawayo': Bulawayo, 'zimbabwean_towns': zimbabwean_towns,
                   'Mutare': Mutare, 'Gweru': Gweru, 'form': DepotContactForm(), 'depot': depot_id})
       

    return render(request, 'noic/depots.html',
                  {'depots': depots, 'add_user' : 'hide', 'Harare': Harare, 'Bulawayo': Bulawayo, 'zimbabwean_towns': zimbabwean_towns,
                   'Mutare': Mutare, 'Gweru': Gweru, 'form1': form1, 'form': DepotContactForm()})


@login_required()
def edit_depot(request, id):
    if request.method == 'POST':
        if NoicDepot.objects.filter(id=id).exists():
            depot_update = NoicDepot.objects.filter(id=id).first()
            depot_update.name = request.POST['name']
            depot_update.address = request.POST['address']
            depot_update.opening_time = request.POST['opening_time']
            depot_update.closing_time = request.POST['closing_time']
            depot_update.save()
            action = "Updating Depot"
            description = f"You have updated NOIC Depot {depot_update.name}"
            Activity.objects.create(depot=depot_update, user=request.user,
                                        action=action, description=description, reference_id=depot_update.id)
            messages.success(request, 'Depot updated successfully')
            return redirect('noic:depots')
        else:
            messages.success(request, 'Depot does not exists')
            return redirect('noic:depots')


@login_required()
def delete_depot(request, id):
    if request.method == 'POST':
        if NoicDepot.objects.filter(id=id).exists():
            depot_update = NoicDepot.objects.filter(id=id).first()
            depot_update.delete()
            action = "Deleting Depot"
            description = f"You have deleted NOIC Depot {depot_update.name}"
            Activity.objects.create(depot=depot_update, user=request.user,
                                        action=action, description=description, reference_id=depot_update.id)
            messages.success(request, 'Depot deleted successfully')
            return redirect('noic:depots')

        else:
            messages.success(request, 'Depot does not exists')
            return redirect('noic:depots')


@login_required()
def fuel_update(request, id):
    fuel_update = DepotFuelUpdate.objects.filter(id=id).first()
    if request.method == 'POST':
        if request.POST['fuel_type'].lower() == 'petrol':
            if request.POST['currency'] == 'USD':
                fuel_update.usd_petrol += float(request.POST['quantity'])
                fuel_update.usd_petrol_price = request.POST['price']
                fuel_update.save()

                action = "Fuel Allocation"
                description = f"You have allocated fuel to {fuel_update.depot.name}"
                Activity.objects.create(depot=fuel_update.depot, user=request.user,
                                    action=action, description=description, reference_id=fuel_update.id)
                messages.success(request, 'updated petrol quantity successfully')
                return redirect('noic:dashboard')
            else:
                fuel_update.rtgs_petrol += float(request.POST['quantity'])
                fuel_update.rtgs_petrol_price = request.POST['price']
                fuel_update.save()

                action = "Fuel Allocation"
                description = f"You have allocated fuel to {fuel_update.depot.name}"
                Activity.objects.create(depot=fuel_update.depot, user=request.user,
                                    action=action, description=description, reference_id=fuel_update.id)
                messages.success(request, 'updated petrol quantity successfully')
                return redirect('noic:dashboard')
            
        else:
            if request.POST['currency'] == 'USD':
                fuel_update.usd_diesel += float(request.POST['quantity'])
                fuel_update.usd_diesel_price = request.POST['price']
                fuel_update.save()

                action = "Fuel Allocation"
                description = f"You have allocated fuel to {fuel_update.depot.name}"
                Activity.objects.create(depot=fuel_update.depot, user=request.user,
                                    action=action, description=description, reference_id=fuel_update.id)
                messages.success(request, 'updated diesel quantity successfully')
                return redirect('noic:dashboard')
            else:
                fuel_update.rtgs_diesel += float(request.POST['quantity'])
                fuel_update.rtgs_diesel_price = request.POST['price']
                fuel_update.save()
                action = "Fuel Allocation"
                description = f"You have allocated fuel to {fuel_update.depot.name}"
                Activity.objects.create(depot=fuel_update.depot, user=request.user,
                                    action=action, description=description, reference_id=fuel_update.id)
                messages.success(request, 'updated diesel quantity successfully')
                return redirect('noic:dashboard')


@login_required()
def edit_prices(request, id):
    fuel_update = DepotFuelUpdate.objects.filter(id=id).first()
    if request.method == 'POST':
        fuel_update.usd_petrol_price = request.POST['usd_petrol_price']
        fuel_update.usd_diesel_price = request.POST['usd_diesel_price']
        fuel_update.rtgs_petrol_price = request.POST['rtgs_petrol_price']
        fuel_update.rtgs_diesel_price = request.POST['rtgs_diesel_price']
        fuel_update.save()

        action = "Updating Prices"
        description = f"You have updated fuel prices for {depot_update.depot.name}"
        Activity.objects.create(depot=fuel_update.depot, user=request.user,
                                    action=action, description=description, reference_id=fuel_update.depot.id)
        messages.success(request, 'updated prices successfully')
        return redirect('noic:dashboard')


@login_required()
def payment_approval(request, id):
    order = Order.objects.filter(id=id).first()
    order.payment_approved = True
    order.save()
    messages.success(request, 'payment approved successfully')
    return redirect('noic:orders')
            

@login_required()
def allocate_fuel(request, id):
    order = Order.objects.filter(id=id).first()
   
    if request.method == 'POST':
        if request.POST['fuel_type'].lower() == 'petrol':
            if request.POST['currency'] == 'USD':
                noic_capacity = NationalFuelUpdate.objects.filter(currency='USD').first()
                if float(request.POST['quantity']) > noic_capacity.unallocated_petrol:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_petrol}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_petrol -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.usd_petrol_price = noic_capacity.petrol_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()

                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')
            
            else:
                noic_capacity = NationalFuelUpdate.objects.filter(currency='RTGS').first()
                if float(request.POST['quantity']) > noic_capacity.unallocated_petrol:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_petrol}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_petrol -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.petrol_price = noic_capacity.petrol_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')
            

        else:
            if request.POST['currency'] == 'USD':
                noic_capacity = NationalFuelUpdate.objects.filter(currency='USD').first()
                if float(request.POST['quantity']) > noic_capacity.unallocated_diesel:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_diesel}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.usd_diesel_price = noic_capacity.diesel_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')
            
            
            else:
                noic_capacity = NationalFuelUpdate.objects.filter(currency='RTGS').first()
                if float(request.POST['quantity']) > noic_capacity.unallocated_diesel:
                    messages.warning(request, f'you cannot allocate fuel more than your capacity of {noic_capacity.unallocated_diesel}L')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company, fuel_type=request.POST['fuel_type'], currency=request.POST['currency'], quantity=float(request.POST['quantity']))
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no, action_no=0, action='Receiving Fuel',fuel_type=sord_object.fuel_type, payment_type=sord_object.currency, initial_quantity=float(request.POST['quantity']), end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.diesel_price = noic_capacity.diesel_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'fuel allocated successfully')
                    return redirect('noic:orders')


@login_required()
def statistics(request):
    yesterday = date.today() - timedelta(days=1)
    monthly_rev = get_aggregate_monthly_sales(datetime.now().year)
    weekly_rev = get_weekly_sales(True)
    last_week_rev = get_weekly_sales(False)
    city_sales_volume = get_volume_sales_by_location()
    final_desperate_cities = []
    desperate_cities = desperate()
    return render(request, 'noic/statistics.html', {'monthly_rev':monthly_rev,'weekly_rev':weekly_rev,'last_week_rev': last_week_rev, 'city_sales_volume': city_sales_volume })


@login_required()
def staff(request):
    staffs = User.objects.filter(user_type='NOIC_STAFF').all()
    for staff in staffs:
        staff.depot = NoicDepot.objects.filter(id=staff.subsidiary_id).first()
    form1 = DepotContactForm()
    depots = NoicDepot.objects.all()
    form1.fields['depot'].choices = [((depot.id, depot.name)) for depot in depots]

    if request.method == 'POST':

        form1 = DepotContactForm(request.POST)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        sup = User.objects.filter(email=email).first()
        if sup is not None:
            messages.warning(request, f"{sup.email} already used in the system, please use a different email")
            return redirect('noic:staff')

        password = random_password()
        phone_number = request.POST.get('phone_number')
        subsidiary_id = request.POST.get('depot')
        
        full_name = first_name + " " + last_name
        i = 0
        username = initial_username = first_name[0] + last_name
        while User.objects.filter(username=username.lower()).exists():
            username = initial_username + str(i)
            i += 1
        user = User.objects.create(company_position='manager', subsidiary_id=subsidiary_id, username=username.lower(),
                                   first_name=first_name, last_name=last_name, user_type='NOIC_STAFF', email=email,
                                   phone_number=phone_number, password_reset=True)
        user.set_password(password)
        depot = NoicDepot.objects.filter(id=subsidiary_id).first()
        depot.is_active = True
        depot.save()

        action = "Creating Staff"
        description = f"You have created user {user.first_name} for {depot.name}"
        Activity.objects.create(depot=depot, user=request.user,
                                    action=action, description=description, reference_id=user.id)
        if message_is_send(request, user, password):
            if user.is_active:
                user.stage = 'menu'
                user.save()

            else:
                messages.warning(request, f"Oops , something went wrong, please try again")
        return redirect('noic:staff')

    return render(request, 'noic/staff.html', {'depots': depots, 'form1': form1, 'staffs': staffs})


@login_required()
def message_is_send(request, user, password):
    sender = "intelliwhatsappbanking@gmail.com"
    subject = 'Fuel Finder Registration'
    message = f"Dear {user.first_name}  {user.last_name}. \nYour Username is: {user.username}\nYour Initial Password is: {password} \n\nPlease login on Fuel Management System Website and access your assigned Depot & don't forget to change your password on user profile. \n. "
    try:
        msg = EmailMultiAlternatives(subject, message, sender, [f'{user.email}'])
        msg.send()
        messages.success(request, f"{user.first_name}  {user.last_name} Registered successfully")
        return True
    except Exception as e:
        messages.warning(request,
                         f"Oops , something wen't wrong sending email, please make sure you have internet access")
        return False
    return render(request, 'buyer/send_email.html')


@login_required()
def report_generator(request):

    '''View to dynamically render form tables based on different criteria'''
    allocations = requests = orders = stock = None
    # orders = Transaction.objects.filter(supplier__company=request.user.company).all()
    start_date = start = "December 1 2019"
    end_date = end = "January 1 2019"

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            start_date = start_date.date()
        report_type = request.POST.get('report_type')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date.date()
        if request.POST.get('report_type') == 'Stock':
            stock = CompanyFuelUpdate.objects.filter(company=request.user.company).all()

            requests = None
            allocations = None
            orders = None
            revs = None
            verified_companies=None
            unverified_companies=None
        if request.POST.get('report_type') == 'Orders':
            orders = Order.objects.filter(date__range=[start_date, end_date])
            print('I am in orders')
            requests = None
            allocations = None
            revs = None
            verified_companies=None
            unverified_companies=None
        if request.POST.get('report_type') == 'Requests':
            requests = FuelRequest.objects.filter(date__range=[start_date, end_date])
            print(f'__________________{requests}__________________________________')
            orders = None
            allocations = None
            stock = None
            revs = None
            verified_companies=None
            unverified_companies=None
        if request.POST.get('report_type') == 'Companies - Verified':
            v_companies = Company.objects.filter(is_verified=True)
            verified_companies = []

            for company in v_companies:
                company.admin = User.objects.filter(company=company).first()
                verified_companies.append(company)


            print(f'__________________{verified_companies}__________________________________')
            orders = None
            allocations = None
            stock = None
            revs = None
            unverified_companies=None
        if request.POST.get('report_type') == 'Companies - Unverified':
            uv_companies = Company.objects.filter(is_verified=False)
            unverified_companies = []

            for company in uv_companies:
                company.admin = User.objects.filter(company=company).first()
                unverified_companies.append(company)


            print(f'__________________{unverified_companies}__________________________________')
            orders = None
            allocations = None
            stock = None
            revs = None
            verified_companies=None
        if request.POST.get('report_type') == 'Allocations':
            print("__________________________I am in allocations____________________________")
            allocations = NationalFuelUpdate.objects.all()
            print(f'________________________________{allocations}__________________________')
            requests = None
            revs = None
            stock = None
            verified_companies=None
            unverified_companies=None
        start = start_date
        end = end_date
    return render(request, 'noic/reports.html')


@login_required()
def profile(request):
    user = request.user
    return render(request, 'noic/profile.html', {'user':user})


@login_required()
def report_generator(request):
    '''View to dynamically render form tables based on different criteria'''
    orders = pending_orders = complete_orders = stock = allocations_per_supplier = None

    # orders = Transaction.objects.filter(supplier__company=request.user.company).all()
    start_date = start = "December 1 2019"
    end_date = end = "January 1 2019"

    if request.method == "POST":
        start_date = request.POST.get('start_date') 
        end_date = request.POST.get('end_date')
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            start_date = start_date.date()
        report_type = request.POST.get('report_type')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date.date()
        if request.POST.get('report_type') == 'Stock':
            stock = type('test', (object,), {})()
            stock.date = datetime.today()
            stock.usd, stock.zwl = get_current_usd_stock(), get_current_zwl_stock()

            allocations_per_supplier = None
            pending_orders = None
            orders = None
            complete_orders = None    

        if request.POST.get('report_type') == 'Pending Orders':
            pending_orders = Order.objects.filter(date__range=[start_date, end_date],
                                               payment_approved=False)
            stock = None
            allocations_per_supplier = None
            orders = None
            complete_orders = None    

        if request.POST.get('report_type') == 'All Orders':
            orders = Order.objects.filter(date__range=[start_date, end_date])
            print(f'__________________{orders}__________________________________')
            print(f'__________________I am in Orders__________________________________')

            pending_orders = None
            allocations_per_supplier = None
            stock = None
            complete_orders = None    

        if request.POST.get('report_type') == 'Completed Orders':
            complete_orders = Order.objects.filter(date__range=[start_date, end_date], payment_approved=True)
            print(f'__________________{complete_orders}__________________________________')
            print(f'__________________I am in complete_orders__________________________________')

            pending_orders = None
            allocations_per_supplier = None
            stock = None
            orders = None    
        if request.POST.get('report_type') == 'Allocations Per Supplier':
            print("__________________________I am in allocations per supplier____________________________")
            allocations = FuelAllocation.objects.all()
            supplier_allocations = User.objects.filter(user_type='S_ADMIN')
            allocations_per_supplier=[]
            for supplier in supplier_allocations:
                order_count = 0
                order_quantity = 0
                for order in SordNationalAuditTrail.objects.filter(company=supplier.company):
                    order_count += 1
                    order_quantity += order.quantity
                supplier.order_count = order_count
                supplier.order_quantity = order_quantity
                if supplier not in allocations_per_supplier:
                    allocations_per_supplier.append(supplier)      

            print(f'________________________________{allocations_per_supplier}__________________________')
            pending_orders = None
            orders = None
            complete_orders = None    
            stock = None
        start = start_date
        end = end_date

        # revs = 0
        return render(request, 'noic/reports.html',
                      {'orders': orders, 'pending_orders': pending_orders, 'complete_orders': complete_orders,
                       'start': start, 'end': end, 'stock': stock, 'allocations_per_supplier':allocations_per_supplier})

    show = False
    return render(request, 'noic/reports.html',
                  {'orders': orders, 'pending_orders': pending_orders, 'complete_orders': complete_orders,
                       'start': start, 'end': end, 'stock': stock})


@login_required()
def statistics(request):
    yesterday = datetime.today() - timedelta(days=1)
    monthly_rev = get_aggregate_monthly_sales(datetime.now().year)
    weekly_rev = get_weekly_sales(True)
    last_week_rev = get_weekly_sales(False)
    city_sales_volume = get_volume_sales_by_location()
    final_desperate_cities = []
    desperate_cities = desperate()
    unallocated_diesel_usd = get_current_usd_stock().diesel_quantity
    unallocated_petrol_usd = get_current_usd_stock().petrol_quantity
    unallocated_diesel_zwl = get_current_zwl_stock().diesel_quantity
    unallocated_petrol_zwl = get_current_zwl_stock().petrol_quantity

    total_allocations_quantity = get_total_allocations()
    orders_complete_percentage = get_complete_orders_percentage
    orders_this_week_count = orders_made_this_week() 
    orders_number = total_orders()
    monthly_rev = get_monthly_orders()

    fuel_orders = Order.objects.filter(payment_approved=True).annotate(
        number_of_orders=Count('company')).order_by('-number_of_orders')
    all_clients = [order.company for order in fuel_orders]

    all_clients = []
    for client in all_clients:
        total_transactions = all_clients.count(client)
        all_clients.remove(client)
        new_client_orders = Order.objects.filter(company=client, payment_approved=True).all()
        total_value = 0
        total_client_orders = []
        number_of_orders = 0
        for tran in new_client_orders:
            total_value += (tran.quantity)
            total_client_orders.append(tran)
            number_of_orders += 1
        client.total_revenue = total_value
        client.total_client_orders = total_client_orders
        client.number_of_orders = total_transactions
        if client not in all_clients:
            all_clients.append(clieny)

    clients = sorted(all_clients, key=lambda x: x.total_revenue, reverse=True)
    
    return render(request, 'noic/statistics.html', {'unallocated_diesel_usd':unallocated_diesel_usd,'unallocated_petrol_usd': unallocated_petrol_usd,
                            'total_allocations_quantity':total_allocations_quantity, 'orders_complete_percentage': orders_complete_percentage,
                            'orders_this_week_count':orders_this_week_count, 'orders_number':orders_number, 'monthly_rev': monthly_rev,
                             'clients':clients, 'unallocated_diesel_zwl':unallocated_diesel_zwl, 'unallocated_petrol_zwl': unallocated_petrol_zwl })
