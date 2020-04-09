from datetime import date

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from validate_email import validate_email

from accounts.models import AccountHistory
from comments.models import Comment
from company.models import Company
from .models import FuelPrices
from fuelUpdates.models import SordCompanyAuditTrail
from fuelfinder.helper_functions import random_password
from national.models import DepotFuelUpdate, NoicDepot, SordNationalAuditTrail
from supplier.models import SubsidiaryFuelUpdate, FuelAllocation, DeliverySchedule
from users.models import SordActionsAuditTrail, Activity
from users.views import message_is_sent
from .constants import coordinates_towns, towns
from .decorators import user_role, user_permission

user = get_user_model()

from .lib import *


@login_required()
@user_role
def dashboard(request):
    zimbabwean_towns = ["Select City ---", "Harare", "Bulawayo", "Gweru", "Mutare", "Chirundu", "Bindura", "Beitbridge",
                        "Hwange", "Juliusdale", "Kadoma", "Kariba", "Karoi", "Kwekwe", "Marondera", "Masvingo",
                        "Chinhoyi", "Mutoko", "Nyanga", "Victoria Falls"]
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
            city = request.POST.get('city')
            address = request.POST.get('address')
            vat_number = request.POST.get('vat_number')
            contact_person = request.POST.get('contact_person')
            account_number = request.POST.get('account_number')
            phone_number = request.POST.get('phone_number')
            new_company = Company.objects.create(name=name, city=city, address=address, license_number=license_number,
                                                 vat_number=vat_number,
                                                 contact_person=contact_person, account_number=account_number,
                                                 company_type='SUPPLIER', phone_number=phone_number, is_active=True)
            new_company.save()
            CompanyFuelUpdate.objects.create(company=new_company)

            action = "Company Registration"
            description = f"You have registered another supplier company {new_company.name}"
            Activity.objects.create(company=new_company, user=request.user, action=action, description=description,
                                    reference_id=new_company.id)
            messages.success(request, 'Company successfully registered.')
            return render(request, 'zeraPortal/companies.html',
                          {'companies': companies, 'new_company': new_company, 'administrater': 'show',
                           'zimbabwean_towns': zimbabwean_towns})
        else:
            messages.warning(request, 'License number already exists.')
            return redirect('zeraPortal:dashboard')
    return render(request, 'zeraPortal/companies.html',
                  {'companies': companies, 'administrater': 'hide', 'zimbabwean_towns': zimbabwean_towns})


@login_required()
@user_role
def activity(request):
    activities = Activity.objects.filter(user=request.user).all()
    return render(request, 'zeraPortal/activity.html', {'activities': activities})


@login_required()
def fuel_prices(request):
    prices = FuelPrices.objects.first()

    if request.method == 'POST':
        if request.POST.get('fuel_type') == 'usd_diesel':
            prices.usd_diesel_vat = request.POST['vat']
            prices.usd_diesel_duty = request.POST['duty']
            prices.usd_diesel_price = request.POST['price']
            prices.save()
            messages.success(request, 'price updated successfully')
            return redirect('zeraPortal:fuel_prices')
        
        elif request.POST.get('fuel_type') == 'rtgs_diesel':
            prices.rtgs_diesel_vat = request.POST['vat']
            prices.rtgs_diesel_duty = request.POST['duty']
            prices.rtgs_diesel_price = request.POST['price']
            prices.save()
            messages.success(request, 'price updated successfully')
            return redirect('zeraPortal:fuel_prices')
        
        elif request.POST.get('fuel_type') == 'usd_petrol':
            prices.usd_petrol_vat = request.POST['vat']
            prices.usd_petrol_duty = request.POST['duty']
            prices.usd_petrol_price = request.POST['price']
            prices.save()
            messages.success(request, 'price updated successfully')
            return redirect('zeraPortal:fuel_prices')
        
        else:
            prices.rtgs_petrol_vat = request.POST['vat']
            prices.rtgs_petrol_duty = request.POST['duty']
            prices.rtgs_petrol_price = request.POST['price']
            prices.save()
            messages.success(request, 'price updated successfully')
            return redirect('zeraPortal:fuel_prices')

    return render(request, 'zeraPortal/prices.html', {'prices': prices})


@login_required()
@user_role
def noic_fuel(request):
    # capacities = NationalFuelUpdate.objects.all()
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

    return render(request, 'zeraPortal/noic_fuel.html',
                  {'depots': depots, 'noic_usd_diesel': noic_usd_diesel, 'noic_rtgs_diesel': noic_rtgs_diesel,
                   'noic_usd_petrol': noic_usd_petrol, 'noic_rtgs_petrol': noic_rtgs_petrol})


@login_required()
def noic_allocations(request, id):
    user_permission(request)
    depot = NoicDepot.objects.filter(id=id).first()
    allocations = SordNationalAuditTrail.objects.filter(assigned_depot=depot).all()
    return render(request, 'zeraPortal/noic_allocations.html', {'allocations': allocations, 'depot': depot})


@login_required()
def edit_company(request, id):
    user_permission(request)
    company = Company.objects.filter(id=id).first()
    license_number = request.POST.get('license_number')
    check_license = Company.objects.filter(~Q(id=id), company_type='SUPPLIER', license_number=license_number).exists()
    if not check_license:
        company.name = request.POST.get('company_name')
        company.city = request.POST.get('city')
        company.address = request.POST.get('address')
        company.vat_number = request.POST.get('vat_number')
        company.contact_person = request.POST.get('contact_person')
        company.account_number = request.POST.get('account_number')
        company.phone_number = request.POST.get('phone_number')
        company.license_number = license_number
        company.save()

        action = "Updating Company"
        description = f"You have updated supplier company {company.name}"
        Activity.objects.create(company=company, user=request.user, action=action, description=description,
                                reference_id=company.id)
        messages.success(request, 'Company details updated successfully.')
        return redirect('zeraPortal:dashboard')
    else:
        messages.warning(request, 'License number already exists.')
        return redirect('zeraPortal:dashboard')


@login_required()
def add_supplier_admin(request, id):
    user_permission(request)
    company = Company.objects.filter(id=id).first()
    print('hhhhhhhhhhh is co', company.name)
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    email = request.POST['email']
    phone_number = request.POST['phone_number']
    check_email = User.objects.filter(email=email).exists()
    is_valid = validate_email(email, verify=True)
    if check_email:
        messages.warning(request, f"Email already used in the system, please use a different email.")
        return redirect('zeraPortal:dashboard')
    # elif not is_valid:
    #     messages.warning(request, 'The email is not valid, Please provide a valid email and try again')
    #     return redirect('zeraPortal:dashboard')
    else:
        i = 0
        username = initial_username = first_name[0] + last_name
        while User.objects.filter(username=username.lower()).exists():
            username = initial_username + str(i)
            i += 1
        password = random_password()
        user = User.objects.create(company=company, first_name=first_name, last_name=last_name, email=email,
                                   phone_number=phone_number.replace(' ', ''),
                                   user_type='S_ADMIN', is_active=True, username=username.lower(), password_reset=True)
        user.set_password(password)
        user.save()
        message_is_sent(request, user, password)

        action = "Creating Supplier Admin"
        description = f"You have created supplier admin for {user.first_name} for {company.name}"
        Activity.objects.create(company=company, user=request.user, action=action, description=description,
                                reference_id=user.id)
        messages.success(request, 'User successfully created.')
        return redirect('zeraPortal:dashboard')


@login_required()
def block_company(request, id):
    user_permission(request)
    company = Company.objects.filter(id=id).first()
    if request.method == 'POST':
        company.is_active = False
        company.save()

        action = "Blocking Company"
        description = f"You have blocked supplier company {company.name}"
        Activity.objects.create(company=company, user=request.user, action=action, description=description,
                                reference_id=company.id)
        messages.success(request, f'{company.name.title()} successfully blocked.')
        return redirect('zeraPortal:dashboard')


@login_required()
def unblock_company(request, id):
    user_permission(request)
    company = Company.objects.filter(id=id).first()
    if request.method == 'POST':
        company.is_active = True
        company.save()

        action = "Unblocking Company"
        description = f"You have unblocked supplier company {company.name}"
        Activity.objects.create(company=company, user=request.user, action=action, description=description,
                                reference_id=company.id)
        messages.success(request, f'{company.name.title()} successfully unblocked.')
        return redirect('zeraPortal:dashboard')


@login_required()
def company_fuel(request):
    user_permission(request)
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


@login_required()
def allocations(request, id):
    user_permission(request)
    sord_allocations = SordCompanyAuditTrail.objects.filter(company__id=id).all()
    return render(request, 'zeraPortal/fuel_allocations.html', {'sord_allocations': sord_allocations})


@login_required()
def sordactions(request, id):
    user_permission(request)
    sord_actions = SordActionsAuditTrail.objects.filter(sord_num=id).all()

    if sord_actions:
        sord_number = sord_actions[0].sord_num
    else:
        sord_number = "-"
    return render(request, 'zeraPortal/sord_actions.html', {'sord_number': sord_number, 'sord_actions': sord_actions})


@login_required()
def download_release_note(request, id):
    user_permission(request)
    document = AccountHistory.objects.filter(id=id).first()
    if document:
        filename = document.release_note.name.split('/')[-1]
        response = HttpResponse(document.release_note, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document Not Found.')
        return redirect(f'/buyer:ayment_release_notes/{document.transaction.id}')
    return response


@login_required()
def transactions(request, id):
    user_permission(request)
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


@login_required()
def payment_and_schedules(request, id):
    user_permission(request)
    transaction = Transaction.objects.filter(id=id).first()
    payment_history = AccountHistory.objects.filter(transaction=transaction).all()
    return render(request, 'zeraPortal/payment_and_schedules.html', {'payment_history': payment_history})


@login_required()
def view_confirmation_doc(request, id):
    user_permission(request)
    delivery = DeliverySchedule.objects.filter(id=id).first()
    if delivery:
        filename = delivery.confirmation_document.name.split('/')[-1]
        response = HttpResponse(delivery.confirmation_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        redirect('zeraPortal:payment_and_schedules')
    return response


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
        redirect('zeraPortal:payment_and_schedules')
    return response


@login_required()
def company_subsidiaries(request, id):
    user_permission(request)
    subsidiaries = Subsidiaries.objects.filter(company__id=id).all()
    company = Company.objects.get(id=id)
    for subsidiary in subsidiaries:
        subsidiary.fuel = SubsidiaryFuelUpdate.objects.filter(subsidiary=subsidiary).first()

    return render(request, 'zeraPortal/company_subsidiaries.html', {'subsidiaries': subsidiaries, 'company': company})


@login_required()
def download_application(request, id):
    user_permission(request)
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if subsidiary:
        filename = subsidiary.application_form.name.split('/')[-1]
        response = HttpResponse(subsidiary.application_form, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect(f'/zeraPortal/company-subsidiaries/{subsidiary.company.id}')
    return response


@login_required()
def download_council(request, id):
    user_permission(request)
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if subsidiary:
        filename = subsidiary.council_approval.name.split('/')[-1]
        response = HttpResponse(subsidiary.council_approval, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect(f'/zeraPortal/company-subsidiaries/{subsidiary.company.id}')
    return response


@login_required()
def download_pop(request, id):
    user_permission(request)
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if subsidiary:
        filename = subsidiary.proof_of_payment.name.split('/')[-1]
        response = HttpResponse(subsidiary.proof_of_payment, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect(f'/zeraPortal/company-subsidiaries/{subsidiary.company.id}')
    return response


@login_required()
def download_fire_brigade_doc(request, id):
    user_permission(request)
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if subsidiary:
        filename = subsidiary.fire_brigade.name.split('/')[-1]
        response = HttpResponse(subsidiary.fire_brigade, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect(f'/zeraPortal/company-subsidiaries/{subsidiary.company.id}')
    return response


@login_required()
def download_ema(request, id):
    user_permission(request)
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if subsidiary:
        filename = subsidiary.ema.name.split('/')[-1]
        response = HttpResponse(subsidiary.ema, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect(f'/zeraPortal/company-subsidiaries/{subsidiary.company.id}')
    return response


@login_required()
def subsidiaries(request):
    user_permission(request)
    subsidiaries = Subsidiaries.objects.all()
    for subsidiary in subsidiaries:
        subsidiary.fuel = SubsidiaryFuelUpdate.objects.filter(subsidiary=subsidiary).first()

    return render(request, 'zeraPortal/subsidiaries.html', {'subsidiaries': subsidiaries})


@login_required()
def change_licence(request, id):
    user_permission(request)
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if request.method == 'POST':
        license_num = request.POST['license_num']
        check_license = Subsidiaries.objects.filter(license_num=license_num).exists()
        if not check_license:
            subsidiary.license_num = license_num
            subsidiary.save()

            action = "Updating Licence"
            description = f"You have updated licence for subsidiary {subsidiary.name}"
            Activity.objects.create(subsidiary=subsidiary, user=request.user, action=action, description=description,
                                    reference_id=subsidiary.id)
            messages.success(request, f'{subsidiary.name.title()} license updated successfully.')
            return redirect(f'/zeraPortal/company-subsidiaries/{subsidiary.company.id}')
        else:
            messages.warning(request, 'License number already exists.')
            return redirect(f'/zeraPortal/company-subsidiaries/{subsidiary.company.id}')


@login_required()
def block_licence(request, id):
    user_permission(request)
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if request.method == 'POST':
        subsidiary.is_active = False
        subsidiary.save()

        action = "Cancelling Licence"
        description = f"You have cancelled licence for subsidiary {subsidiary.name}"
        Activity.objects.create(subsidiary=subsidiary, user=request.user, action=action, description=description,
                                reference_id=subsidiary.id)
        messages.info(request, f'{subsidiary.name.title()}"s license blocked successfully.')
        return redirect(f'/zeraPortal/company-subsidiaries/{subsidiary.company.id}')


@login_required()
def download_proof(request, id):
    user_permission(request)
    document = AccountHistory.objects.filter(id=id).first()
    if document:
        filename = document.proof_of_payment.name.split('/')[-1]
        response = HttpResponse(document.proof_of_payment, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document Not Found')
        return redirect(f'/zeraPortal/payment_and_schedules/{document.transaction.id}')
    return response


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
        redirect(f'/zeraPortal/payment_and_schedules/{delivery.transaction.id}')
    return response


@login_required()
def view_release_note(request, id):
    user_permission(request)
    payment = AccountHistory.objects.filter(id=id).first()
    payment.quantity = float(payment.value) / float(payment.transaction.offer.price)
    context = {
        'payment': payment
    }
    return render(request, 'zeraPortal/release_note.html', context=context)


@login_required()
def noic_release_note(request, id):
    user_permission(request)
    allocation = SordNationalAuditTrail.objects.filter(id=id).first()
    allocation.admin = User.objects.filter(company=allocation.company).filter(user_type='S_ADMIN').first()
    allocation.rep = request.user
    context = {
        'allocation': allocation
    }
    return render(request, 'zeraPortal/noic_release_note.html', context=context)


@login_required()
def noic_delivery_note(request, id):
    user_permission(request)
    delivery = SordNationalAuditTrail.objects.filter(id=id).first()
    if delivery:
        filename = delivery.d_note.name.split('/')[-1]
        response = HttpResponse(delivery.d_note, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found')
        redirect(f'/zeraPortal/noic_allocations/{delivery.assigned_depot.id}')
    return response


@login_required()
def unblock_licence(request, id):
    user_permission(request)
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if request.method == 'POST':
        subsidiary.is_active = True
        subsidiary.save()

        action = "Unblocking Licence"
        description = f"You have unblocked licence for subsidiary {subsidiary.name}"
        Activity.objects.create(subsidiary=subsidiary, user=request.user, action=action, description=description,
                                reference_id=subsidiary.id)
        messages.success(request, f'{subsidiary.name.title()}"s license unblocked successfully.')
        return redirect(f'/zeraPortal/company-subsidiaries/{subsidiary.company.id}')


@login_required()
def add_licence(request, id):
    user_permission(request)
    subsidiary = Subsidiaries.objects.filter(id=id).first()
    if request.method == 'POST':
        license_num = request.POST['license_num']
        check_license = Subsidiaries.objects.filter(license_num=license_num).exists()
        if not check_license:
            subsidiary.license_num = license_num
            subsidiary.is_active = True
            subsidiary.save()

            action = "Approving Subsidiary"
            description = f"You have approved subsidiary {subsidiary.name}"
            Activity.objects.create(subsidiary=subsidiary, user=request.user, action=action, description=description,
                                    reference_id=subsidiary.id)
            messages.success(request, f'{subsidiary.name.title()} approved successfully.')
            return redirect(f'/zeraPortal/company-subsidiaries/{subsidiary.company.id}')
        else:
            messages.warning(request, 'License number already exists.')
            return redirect(f'/zeraPortal/company-subsidiaries/{subsidiary.company.id}')


@login_required()
@user_role
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
            stock = CompanyFuelUpdate.objects.all()

            requests = None
            allocations = None
            trans = None
            revs = None
            verified_companies = None
            unverified_companies = None
        if request.POST.get('report_type') == 'Transactions' or request.POST.get('report_type') == 'Revenue':
            trans = Transaction.objects.filter(date__range=[start_date, end_date])
            requests = None
            allocations = None
            revs = None
            verified_companies = None
            unverified_companies = None

            if request.POST.get('report_type') == 'Revenue':
                trans = Transaction.objects.filter(date__range=[start_date, end_date],
                                                   supplier__company=request.user.company, is_complete=True)
                revs = {}
                total_revenue = 0
                trans_no = 0

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
            verified_companies = None
            unverified_companies = None
        if request.POST.get('report_type') == 'Companies - Verified':
            v_companies = Company.objects.filter(is_verified=True, company_type='SUPPLIER')
            verified_companies = []

            for company in v_companies:
                company.admin = User.objects.filter(company=company).first()
                verified_companies.append(company)

            print(f'__________________{verified_companies}__________________________________')
            trans = None
            allocations = None
            stock = None
            revs = None
            unverified_companies = None
        if request.POST.get('report_type') == 'Companies - Unverified':
            uv_companies = Company.objects.filter(is_verified=False, company_type='SUPPLIER')
            unverified_companies = []

            for company in uv_companies:
                company.admin = User.objects.filter(company=company).first()
                unverified_companies.append(company)

            print(f'__________________{unverified_companies}__________________________________')
            trans = None
            allocations = None
            stock = None
            revs = None
            verified_companies = None
        if request.POST.get('report_type') == 'Allocations':
            print("__________________________I am in allocations____________________________")
            allocations = FuelAllocation.objects.all()
            print(f'________________________________{allocations}__________________________')
            requests = None
            revs = None
            stock = None
            verified_companies = None
            unverified_companies = None
        start = start_date
        end = end_date

        # revs = 0
        return render(request, 'zeraPortal/reports.html',
                      {'trans': trans, 'requests': requests, 'allocations': allocations,
                       'verified_companies': verified_companies,
                       'unverified_companies': unverified_companies, 'start': start, 'end': end, 'revs': revs,
                       'stock': stock})

    show = False
    print(trans)
    return render(request, 'zeraPortal/reports.html',
                  {'trans': trans, 'requests': requests, 'allocations': allocations,
                   'start': start_date, 'end': end_date, 'show': show, 'stock': stock})


@login_required()
@user_role
def statistics(request):
    yesterday = date.today() - timedelta(days=1)
    monthly_rev = get_aggregate_monthly_sales(datetime.now().year)
    weekly_rev = get_weekly_sales(True)
    last_week_rev = get_weekly_sales(False)
    city_sales_volume = get_volume_sales_by_location()
    final_desperate_cities = []
    desperate_cities = desperate()

    while len(desperate_cities) > 5:
        desperate_cities.popitem()

    for city, deficit in desperate_cities.items():
        final_desperate_cities.append((city, deficit))

    # number_of_companies = Company.objects.all().count()
    # number_of_depots = Subsidiaries.objects.filter(is_depot=True).count()
    # number_of_s_stations = Subsidiaries.objects.filter(is_depot=False).count()
    last_year_rev = get_aggregate_monthly_sales((datetime.now().year - 1))
    # offers = Offer.objects.all().count()
    # bulk_requests = FuelRequest.objects.filter(delivery_method="SELF COLLECTION").count()
    # normal_requests = FuelRequest.objects.filter(delivery_method="DELIVERY").count()  # Change these 2 items
    staff = ''
    # new_orders = FuelRequest.objects.filter(date__gt=yesterday).count()
    # clients = []
    # stock = get_aggregate_stock()
    # diesel = stock['diesel']
    # petrol = stock['petrol']

    trans = Transaction.objects.filter(is_complete=True).annotate(
        number_of_trans=Count('buyer')).order_by('-number_of_trans')[:10]
    buyers = [client.buyer for client in trans]

    branches = Subsidiaries.objects.filter(is_depot=False)

    subs = []

    for sub in branches:
        tran_amount = 0
        sub_trans = Transaction.objects.filter(supplier__subsidiary_id=sub.id, is_complete=True)
        for sub_tran in sub_trans:
            tran_amount += (float(sub_tran.offer.request.amount) * float(sub_tran.offer.price))
        sub.tran_count = sub_trans.count()
        sub.tran_value = tran_amount
        subs.append(sub)

    # sort subsidiaries by transaction value
    sorted_subs = sorted(subs, key=lambda x: x.tran_value, reverse=True)

    new_buyers = []

    for buyer in buyers:
        total_transactions = buyers.count(buyer)
        new_buyer_transactions = Transaction.objects.filter(buyer=buyer, is_complete=True).all()
        total_value = 0
        purchases = []
        for tran in new_buyer_transactions:
            total_value += (float(tran.offer.request.amount) * float(tran.offer.price))
            purchases.append(tran)
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
    # revenue = get_aggregate_total_revenue()
    # revenue = '${:,.2f}'.format(revenue)
    # revenue = str(revenue) + '.00'

    # try:
    #     trans = Transaction.objects.filter(supplier=request.user, complete=true).count()/Transaction.objects.all().count()/100
    # except:
    #     trans = 0    
    # trans_complete = get_aggregate_transactions_complete_percentage()
    # inactive_depots = Subsidiaries.objects.filter(is_active=False, is_depot=True).count()
    # inactive_stations = Subsidiaries.objects.filter(is_active=False, is_depot=False).count()
    # approval_percentage = get_approved_company_complete_percentage()

    return render(request, 'zeraPortal/statistics.html', {'trans': trans, 'clients': clients,
                                                          'monthly_rev': monthly_rev, 'weekly_rev': weekly_rev,
                                                          'last_week_rev': last_week_rev,
                                                          'city_sales_volume': city_sales_volume,
                                                          'final_desperate_cities': final_desperate_cities,
                                                          'sorted_subs': sorted_subs})


@login_required()
def clients_history(request, cid):
    user_permission(request)
    buyer = User.objects.filter(id=cid).first()
    trans = []
    state = 'All'

    if request.method == "POST":

        if request.POST.get('report_type') == 'Complete':
            trns = Transaction.objects.filter(buyer=buyer, is_complete=True)
            trans = []
            for tran in trns:
                tran.revenue = (float(tran.offer.request.amount) * float(tran.offer.price))
                tran.account_history = AccountHistory.objects.filter(transaction=tran).all()
                trans.append(tran)
            state = 'Complete'

        if request.POST.get('report_type') == 'Incomplete':
            trns = Transaction.objects.filter(buyer=buyer, is_complete=False)
            trans = []
            for tran in trns:
                tran.revenue = (float(tran.offer.request.amount) * float(tran.offer.price))
                tran.account_history = AccountHistory.objects.filter(transaction=tran).all()
                trans.append(tran)
            state = 'Incomplete'

        if request.POST.get('report_type') == 'All':
            trns = Transaction.objects.filter(buyer=buyer)
            trans = []
            for tran in trns:
                tran.revenue = (float(tran.offer.request.amount) * float(tran.offer.price))
                trans.append(tran)
            state = 'All'
        return render(request, 'zeraPortal/clients_history.html', {'trans': trans, 'buyer': buyer, 'state': state})

    trns = Transaction.objects.filter(buyer=buyer)
    trans = []
    for tran in trns:
        tran.revenue = (float(tran.offer.request.amount) * float(tran.offer.price))
        trans.append(tran)

    return render(request, 'zeraPortal/clients_history.html', {'trans': trans, 'buyer': buyer, 'state': state})


@login_required()
def subsidiary_transaction_history(request, sid):
    user_permission(request)
    subsidiary = Subsidiaries.objects.filter(id=sid).first()
    trans = []
    state = 'All'

    if request.method == "POST":

        if request.POST.get('report_type') == 'Complete':
            trns = Transaction.objects.filter(supplier__subsidiary_id=subsidiary.id, is_complete=True)
            trans = []
            for tran in trns:
                tran.revenue = (float(tran.offer.request.amount) * float(tran.offer.price))
                trans.append(tran)
            state = 'Complete'

        if request.POST.get('report_type') == 'Incomplete':
            trns = Transaction.objects.filter(supplier__subsidiary_id=subsidiary.id, is_complete=False)
            trans = []
            for tran in trns:
                tran.revenue = (float(tran.offer.request.amount) * float(tran.offer.price))
                trans.append(tran)
            state = 'Incomplete'

        if request.POST.get('report_type') == 'All':
            trns = Transaction.objects.filter(supplier__subsidiary_id=subsidiary.id)
            trans = []
            for tran in trns:
                tran.revenue = (float(tran.offer.request.amount) * float(tran.offer.price))
                trans.append(tran)
            state = 'All'
        return render(request, 'zeraPortal/subsidiary_history.html',
                      {'trans': trans, 'subsidiary': subsidiary, 'state': state})

    trns = Transaction.objects.filter(supplier__subsidiary_id=subsidiary.id)
    for tran in trns:
        tran.revenue = (float(tran.offer.request.amount) * float(tran.offer.price))
        trans.append(tran)

    return render(request, 'zeraPortal/subsidiary_history.html',
                  {'trans': trans, 'subsidiary': subsidiary, 'state': state})


@login_required()
@user_role
def profile(request):
    user = request.user
    return render(request, 'zeraPortal/profile.html', {'user': user})


@login_required()
@user_role
def suspicious_behavior(request):
    schedules = DeliverySchedule.objects.filter(date__lt=datetime.today() + timedelta(days=1),
                                                supplier_document='')
    late_schedules = []
    suspicious_schedules = []

    for ds in DeliverySchedule.objects.all():
        if ds.supplier_document and ds.confirmation_date:
            account = AccountHistory.objects.filter(transaction=ds.transaction)
            if not account:
                suspicious_schedules.append(ds)

    for schedule in schedules:
        d1 = datetime.strptime(str(schedule.date), "%Y-%m-%d")
        d2 = datetime.strptime(str(datetime.today().date()), "%Y-%m-%d")
        schedule.days_late = abs((d2 - d1).days)
        late_schedules.append(schedule)

    return render(request, 'zeraPortal/suspicious_behavior.html',
                  {'late_schedules': late_schedules, 'suspicious_schedules': suspicious_schedules})


@login_required()
@user_role
def desperate_regions(request):
    context = {
        'regions': desperate(),
        'mapping': dict(zip(towns, coordinates_towns))
    }
    return render(request, 'zeraPortal/desperate_regions.html', context=context)


@login_required()
@user_role
def comments(request):
    subsidiaries = []

    for sub in Subsidiaries.objects.filter(is_depot=False):
        sub.comments = Comment.objects.filter(station=sub)
        sub.comments = sub.comments[:5]
        if sub.comments:
            subsidiaries.append(sub)

    return render(request, 'zeraPortal/comments.html', {'subsidiaries': subsidiaries})


@login_required()
def sub_comments(request, id):
    user_permission(request)
    sub = Subsidiaries.objects.filter(id=id).first()
    comments = Comment.objects.filter(station=sub)
    return render(request, 'zeraPortal/sub_comments.html', {'comments': comments, 'sub': sub})
