import secrets
from validate_email import validate_email
from datetime import datetime, timedelta

from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, update_session_auth_hash, login, logout
from datetime import datetime, date
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from itertools import chain
from operator import attrgetter

from buyer.models import User, FuelRequest
from company.models import Company, CompanyFuelUpdate
from supplier.models import Subsidiaries, SubsidiaryFuelUpdate, FuelAllocation, Transaction, Offer, DeliverySchedule
from .forms import ZeraProfileUpdateForm, ZeraImageUpdateForm
from fuelUpdates.models import SordCompanyAuditTrail
from users.models import SordActionsAuditTrail
from accounts.models import AccountHistory
from users.views import message_is_sent

user = get_user_model()

from .lib import *



def dashboard(request):
    companies = Company.objects.filter(company_type='SUPPLIER').all()
    for company in companies:
        company.num_of_depots = Subsidiaries.objects.filter(company=company, is_depot='True').count()
        company.num_of_stations = Subsidiaries.objects.filter(company=company, is_depot='False').count()
        company.check_admin = User.objects.filter(user_type='S_ADMIN', company__id=company.id).exists()
    if request.method == 'POST':
        license_number = request.POST.get('license_number')
        check_license = Company.objects.filter(company_type='SUPPLIER', license_number=license_number).exists()
        if not check_license:
            name = request.POST.get('company_name')
            address = request.POST.get('address')
            destination_bank = request.POST.get('destination_bank')
            iban_number = request.POST.get('iban_number')
            account_number = request.POST.get('account_number')
            new_company = Company.objects.create(name=name, address=address, license_number=license_number, destination_bank=destination_bank,
                                iban_number=iban_number, account_number=account_number, company_type='SUPPLIER', is_active=True)
            new_company.save()
            CompanyFuelUpdate.objects.create(company=new_company)
            messages.success(request, 'Company successfully registered')
            return redirect('zeraPortal:dashboard')
        else:
            messages.warning(request, 'License number already exists!!!')
            return redirect('zeraPortal:dashboard')
    return render(request, 'zeraPortal/companies.html', {'companies': companies})


def add_supplier_admin(request, id):
    company = Company.objects.filter(id=id).first()
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    email = request.POST['email']
    phone_number = request.POST['phone_number']
    check_email = User.objects.filter(email=email).exists()
    is_valid = validate_email(email, verify=True)
    if check_email:
        messages.warning(request, f"Email already used in the system, please use a different email")
        return redirect('zeraPortal:dashboard')
    elif not is_valid:
        messages.warning(request, 'The email is not valid, Please provide a valid email and try again')
        return redirect('zeraPortal:dashboard')
    else:
        i = 0
        username = initial_username = first_name[0] + last_name
        while User.objects.filter(username=username.lower()).exists():
            username = initial_username + str(i)
            i += 1
        password = 'pbkdf2_sha256$150000$fksjasjRlRRk$D1Di/BTSID8xcm6gmPlQ2tZvEUIrQHuYioM5fq6Msgs='
        user = User.objects.create(company=company, first_name=first_name, last_name=last_name, email=email, phone_number=phone_number,
        user_type='S_ADMIN', is_active=True, username=username.lower(), password=password)
        message_is_sent(request, user)
        messages.success(request, 'User successfully created')
        return redirect ('zeraPortal:dashboard')


def block_company(request, id):
    company = Company.objects.filter(id=id).first()
    if request.method == 'POST':
        company.is_active = False
        company.save()
        messages.success(request, f'{company.name} Successfully Blocked')
        return redirect('zeraPortal:dashboard')


def unblock_company(request, id):
    company = Company.objects.filter(id=id).first()
    if request.method == 'POST':
        company.is_active = True
        company.save()
        messages.success(request, f'{company.name} Successfully Unblocked')
        return redirect('zeraPortal:dashboard')


def company_fuel(request):
    capacities = CompanyFuelUpdate.objects.all()
    for fuel in capacities:
        subs_total_diesel_capacity = 0
        subs_total_petrol_capacity = 0
        subsidiaries_fuel = SubsidiaryFuelUpdate.objects.filter(subsidiary__company=fuel.company).all()
        for sub_fuel in subsidiaries_fuel:
            subs_total_diesel_capacity += sub_fuel.diesel_quantity
            subs_total_petrol_capacity += sub_fuel.petrol_quantity

        fuel.diesel_capacity = fuel.unallocated_diesel + subs_total_diesel_capacity
        fuel.petrol_capacity = fuel.unallocated_petrol + subs_total_petrol_capacity

        fuel.diesel_capacity = '{:,}'.format(fuel.diesel_capacity)
        fuel.petrol_capacity = '{:,}'.format(fuel.petrol_capacity)

    return render(request, 'zeraPortal/company_fuel.html', {'capacities': capacities})


def allocations(request, id):
    sord_allocations = SordCompanyAuditTrail.objects.filter(company__id=id).all()
    return render(request, 'zeraPortal/fuel_allocations.html', {'sord_allocations': sord_allocations})


def sordactions(request, id):
    sord_actions = SordActionsAuditTrail.objects.filter(sord_num=id).all()

    if sord_actions:
        sord_number = sord_actions[0].sord_num
    else:
        sord_number = "-"
    return render(request, 'zeraPortal/sord_actions.html', {'sord_number': sord_number, 'sord_actions': sord_actions})


def transactions(request, id):
    today = datetime.now().strftime("%m/%d/%y")
    transporters = Company.objects.filter(company_type="TRANSPORTER").all()
    transactions = []
    company = ""
    for tran in Transaction.objects.filter(supplier__company__id=id).all():
        delivery_sched = DeliverySchedule.objects.filter(transaction=tran).first()
        company = Company.objects.filter(id=tran.supplier.company.id).first()
        tran.depot = Subsidiaries.objects.filter(id=tran.supplier.subsidiary_id).first()
        if delivery_sched:
            tran.delivery_sched = delivery_sched
        transactions.append(tran)
    context = {
        'transactions': transactions,
        'transporters': transporters,
        'today': today,
        'company': company
    }
    return render(request, 'zeraPortal/transactions.html', context=context)


def payment_and_schedules(request, id):
    transaction = Transaction.objects.filter(id=id).first()
    payment_history = AccountHistory.objects.filter(transaction=transaction).all()
    return render(request, 'zeraPortal/payment_and_schedules.html', {'payment_history': payment_history})


def view_confirmation_doc(request, id):
    delivery = DeliverySchedule.objects.filter(id=id).first()
    if delivery:
        filename = delivery.confirmation_document.name.split('/')[-1]
        response = HttpResponse(delivery.confirmation_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document Not Found')
        redirect('zeraPortal:payment_and_schedules')
    return response


def view_supplier_doc(request, id):
    delivery = DeliverySchedule.objects.filter(id=id).first()
    if delivery:
        filename = delivery.supplier_document.name.split('/')[-1]
        response = HttpResponse(delivery.supplier_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document Not Found')
        redirect('zeraPortal:payment_and_schedules')
    return response


def company_subsidiaries(request, id):
    subsidiaries = Subsidiaries.objects.filter(company__id=id).all()
    for subsidiary in subsidiaries:
        subsidiary.fuel = SubsidiaryFuelUpdate.objects.filter(subsidiary=subsidiary).first()
        if subsidiary.license_num.strip() == "":
            subsidiary.license_num = None
    return render(request, 'zeraPortal/company_subsidiaries.html', {'subsidiaries':subsidiaries})


def subsidiaries(request):
    subsidiaries = Subsidiaries.objects.all()
    for subsidiary in subsidiaries:
        subsidiary.fuel = SubsidiaryFuelUpdate.objects.filter(subsidiary=subsidiary).first()
        # if subsidiary.license_num.strip() == "":
        #     subsidiary.license_num = None
    return render(request, 'zeraPortal/subsidiaries.html', {'subsidiaries':subsidiaries})


def change_licence(request, id):
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if request.method == 'POST':
        license_num = request.POST['license_num']
        check_license = Subsidiaries.objects.filter(license_num=license_num).exists()
        if not check_license:
            subsidiary.license_num = license_num
            subsidiary.save()
            messages.success(request, f'{subsidiary.name} License updated successfully')
            return redirect('zeraPortal:subsidiaries')
        else:
            messages.warning(request, 'License number already exists!!')
            return redirect('zeraPortal:subsidiaries')


def block_licence(request, id):
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if request.method == 'POST':
        subsidiary.is_active = False
        subsidiary.save()
        messages.info(request, f'{subsidiary.name} License Blocked')
        return redirect('zeraPortal:subsidiaries')


def unblock_licence(request, id):
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if request.method == 'POST':
        subsidiary.is_active = True
        subsidiary.save()
        messages.success(request, f'{subsidiary.name} License unblocked successfully')
        return redirect('zeraPortal:subsidiaries')


def add_licence(request, id):
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if request.method == 'POST':
        license_num =  request.POST['license_num']
        check_license = Subsidiaries.objects.filter(license_num=license_num).exists()
        if not check_license:
            subsidiary.license_num = license_num
            subsidiary.save()
            messages.success(request, f'{subsidiary.name} Approved Successfully')
            return redirect('zeraPortal:subsidiaries')
        else:
            messages.warning(request, 'License number already exists!!')
            return redirect('zeraPortal:subsidiaries')


def report_generator(request):
    '''View to dynamically render form tables based on different criteria'''
    allocations = requests = trans = stock = None
    # trans = Transaction.objects.filter(supplier__company=request.user.company).all()
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
            trans = None
            revs = None
            verified_companies=None
            unverified_companies=None
        if request.POST.get('report_type') == 'Transactions' or request.POST.get('report_type') == 'Revenue':
            trans = Transaction.objects.filter(date__range=[start_date, end_date],
                                               supplier__company=request.user.company)
            requests = None
            allocations = None
            revs = None
            verified_companies=None
            unverified_companies=None

            if request.POST.get('report_type') == 'Revenue':
                trans = Transaction.objects.filter(date__range=[start_date, end_date],
                                                   supplier__company=request.user.company, is_complete=True)
                revs = {}
                total_revenue = 0
                trans_no =0

                if trans:
                    for tran in trans:
                        total_revenue += (tran.offer.request.amount * tran.offer.price)
                        trans_no += 1
                    revs['revenue'] = '${:,.2f}'.format(total_revenue)

                    revs['hits'] = trans_no
                    revs['date'] = datetime.today().strftime('%D')
                trans = None

            requests = None
            allocations = None
            stock = None
        if request.POST.get('report_type') == 'Requests':
            requests = FuelRequest.objects.filter(date__range=[start_date, end_date])
            print(f'__________________{requests}__________________________________')
            trans = None
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
            trans = None
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
            trans = None
            allocations = None
            stock = None
            revs = None
            verified_companies=None
        if request.POST.get('report_type') == 'Allocations':
            print("__________________________I am in allocations____________________________")
            allocations = FuelAllocation.objects.all()
            print(f'________________________________{allocations}__________________________')
            requests = None
            revs = None
            stock = None
            verified_companies=None
            unverified_companies=None
        start = start_date
        end = end_date

        # revs = 0
        return render(request, 'zeraPortal/reports.html',
                      {'trans': trans, 'requests': requests, 'allocations': allocations,'verified_companies':verified_companies,
                       'unverified_companies':unverified_companies,'start': start, 'end': end, 'revs': revs, 'stock': stock})

    show = False
    print(trans)
    return render(request, 'zeraPortal/reports.html',
                  {'trans': trans, 'requests': requests, 'allocations': allocations,
                   'start': start_date, 'end': end_date, 'show': show, 'stock': stock})


def statistics(request):
    yesterday = date.today() - timedelta(days=1)
    monthly_rev = get_aggregate_monthly_sales(datetime.now().year)
    weekly_rev = get_weekly_sales(True)
    last_week_rev = get_weekly_sales(False)
    city_sales_volume = get_volume_sales_by_location()
    number_of_companies = Company.objects.all().count()
    number_of_depots = Subsidiaries.objects.filter(is_depot=True).count()
    number_of_s_stations = Subsidiaries.objects.filter(is_depot=False).count()
    last_year_rev = get_aggregate_monthly_sales((datetime.now().year - 1))
    offers = Offer.objects.all().count()
    bulk_requests = FuelRequest.objects.filter(delivery_method="SELF COLLECTION").count()
    normal_requests = FuelRequest.objects.filter(delivery_method="DELIVERY").count()  # Change these 2 items
    staff = ''
    new_orders = FuelRequest.objects.filter(date__gt=yesterday).count()
    clients = []
    stock = get_aggregate_stock()
    diesel = stock['diesel']
    petrol = stock['petrol']

    trans = Transaction.objects.filter(is_complete=True).annotate(
        number_of_trans=Count('buyer')).order_by('-number_of_trans')[:10]
    buyers = [client.buyer for client in trans]

    branches = Subsidiaries.objects.filter(is_depot=True)

    subs = []

    for sub in branches:
        tran_amount = 0
        sub_trans = Transaction.objects.filter(supplier__subsidiary_id=sub.id,
                                               is_complete=True)
        for sub_tran in sub_trans:
            tran_amount += (sub_tran.offer.request.amount * sub_tran.offer.price)
        sub.tran_count = sub_trans.count()
        sub.tran_value = tran_amount
        subs.append(sub)

    # sort subsidiaries by transaction value
    sorted_subs = sorted(subs, key=lambda x: x.tran_value, reverse=True)

    new_buyers = []
    for buyer in buyers:
        total_transactions = buyers.count(buyer)
        buyers.remove(buyer)
        new_buyer_transactions = Transaction.objects.filter(is_complete=True).all()
        total_value = 0
        purchases = []
        number_of_trans = 0
        for tran in new_buyer_transactions:
            total_value += (tran.offer.request.amount * tran.offer.price)
            purchases.append(tran)
            number_of_trans += 1
        buyer.total_revenue = total_value
        buyer.purchases = purchases
        buyer.number_of_trans = total_transactions
        if buyer not in new_buyers:
            new_buyers.append(buyer)

    clients = sorted(new_buyers, key=lambda x: x.total_revenue, reverse=True)

    # for company in companies:
    #     company.total_value = value[counter]
    #     company.num_transactions = num_trans[counter]
    #     counter += 1

    # clients = [company for company in  companies]

    # revenue = round(float(sum(value)))
    revenue = get_aggregate_total_revenue()
    revenue = '${:,.2f}'.format(revenue)
    # revenue = str(revenue) + '.00'

    # try:
    #     trans = Transaction.objects.filter(supplier=request.user, complete=true).count()/Transaction.objects.all().count()/100
    # except:
    #     trans = 0    
    # trans_complete = get_aggregate_transactions_complete_percentage()
    inactive_depots = Subsidiaries.objects.filter(is_active=False, is_depot=True).count()
    inactive_stations = Subsidiaries.objects.filter(is_active=False, is_depot=False).count()
    approval_percentage = get_approved_company_complete_percentage()

    return render(request, 'zeraPortal/statistics.html', {'offers': offers,
                                                     'bulk_requests': bulk_requests, 'trans': trans, 'clients': clients,
                                                     'normal_requests': normal_requests,
                                                     'diesel': diesel, 'petrol': petrol, 'revenue': revenue,
                                                     'inactive_stations': inactive_stations,'inactive_depots': inactive_depots,
                                                     'sorted_subs': sorted_subs,
                                                     'monthly_rev': monthly_rev, 'weekly_rev': weekly_rev,
                                                     'last_week_rev': last_week_rev, 'number_of_companies': number_of_companies,
                                                     'number_of_depots':number_of_depots, 'number_of_s_stations':number_of_s_stations,
                                                     'approval_percentage': approval_percentage, 'city_sales_volume':city_sales_volume})
    

def clients_history(request, cid):
    buyer = User.objects.filter(id=cid).first()
    trans = []
    state = 'All'

    if request.method == "POST":

        if request.POST.get('report_type') == 'Complete':
            trns = Transaction.objects.filter(buyer=buyer, is_complete=True)
            trans = []
            for tran in trns:
                tran.revenue = tran.offer.request.amount * tran.offer.price
                trans.append(tran)
            state = 'Complete'

        if request.POST.get('report_type') == 'Incomplete':
            trns = Transaction.objects.filter(buyer=buyer, is_complete=False)
            trans = []
            for tran in trns:
                tran.revenue = tran.offer.request.amount * tran.offer.price
                trans.append(tran)
            state = 'Incomplete'

        if request.POST.get('report_type') == 'All':
            trns = Transaction.objects.filter(buyer=buyer)
            trans = []
            for tran in trns:
                tran.revenue = tran.offer.request.amount * tran.offer.price
                trans.append(tran)
            state = 'All'
        return render(request, 'zeraPortal/clients_history.html', {'trans': trans, 'buyer': buyer, 'state': state})

    trns = Transaction.objects.filter(buyer=buyer)
    trans = []
    for tran in trns:
        tran.revenue = tran.offer.request.amount * tran.offer.price
        trans.append(tran)

    return render(request, 'zeraPortal/client_history.html', {'trans': trans, 'buyer': buyer, 'state': state,      
                                                     'approval_percentage': approval_percentage})    


@login_required
def subsidiary_transaction_history(request, sid):
    subsidiary = Subsidiaries.objects.filter(id=sid).first()
    trans = []
    state = 'All'

    if request.method == "POST":

        if request.POST.get('report_type') == 'Complete':
            trns = Transaction.objects.filter(supplier__subsidiary_id=subsidiary.id, is_complete=True)
            trans = []
            for tran in trns:
                tran.revenue = tran.offer.request.amount * tran.offer.price
                trans.append(tran)
            state = 'Complete'

        if request.POST.get('report_type') == 'Incomplete':
            trns = Transaction.objects.filter(supplier__subsidiary_id=subsidiary.id, is_complete=False)
            trans = []
            for tran in trns:
                tran.revenue = tran.offer.request.amount * tran.offer.price
                trans.append(tran)
            state = 'Incomplete'

        if request.POST.get('report_type') == 'All':
            trns = Transaction.objects.filter(supplier__subsidiary_id=subsidiary.id)
            trans = []
            for tran in trns:
                tran.revenue = tran.offer.request.amount * tran.offer.price
                trans.append(tran)
            state = 'All'
        return render(request, 'zeraPortal/subsidiary_history.html', {'trans': trans, 'subsidiary': subsidiary, 'state': state})
    
    trns = Transaction.objects.filter(supplier__subsidiary_id=subsidiary.id)
    for tran in trns:
        tran.revenue = tran.offer.request.amount * tran.offer.price
        trans.append(tran)

    return render(request, 'zeraPortal/subsidiary_history.html', {'trans': trans, 'subsidiary': subsidiary})

def profile(request):
    return render(request, 'zeraPortal/profile.html')


def suspicious_behavior(request):
    schedules = DeliverySchedule.objects.filter(date__lt=datetime.today() + timedelta(days=1), confirmation_document='',
                                                    supplier_document='')
    late_schedules = []
    for schedule in schedules:
        d1 = datetime.strptime(str(schedule.date), "%Y-%m-%d")
        d2 = datetime.strptime(str(datetime.today().date()), "%Y-%m-%d")
        schedule.days_late = abs((d2 - d1).days)
        late_schedules.append(schedule)
        
    return render(request, 'zeraPortal/suspicious_behavior.html', {'late_schedules':late_schedules})