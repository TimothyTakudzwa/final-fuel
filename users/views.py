# import datetime
import secrets
from datetime import datetime, date
from io import BytesIO

import pandas as pd
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import get_template
from django.template.loader import render_to_string
from weasyprint import HTML
import pandas as pd
from xhtml2pdf import pisa
from decimal import *

from accounts.models import Account, AccountHistory
from buyer.forms import *
from company.lib import *
from zeraPortal.lib import convert_to_dataframe
from zeraPortal.models import FuelPrices
from supplier.models import DeliverySchedule
from fuelUpdates.models import SordCompanyAuditTrail
from fuelfinder.helper_functions import random_password
from national.models import Order, SordNationalAuditTrail, DepotFuelUpdate
from notification.models import Notification
from users.models import *
from .decorators import user_role, user_permission
from .forms import SupplierContactForm, UsersUploadForm, ReportForm, ProfileEditForm, ActionForm, DepotContactForm, PasswordChange
from decimal import *

user = get_user_model()
today = date.today()

from fuelfinder import settings


class Render:
    @staticmethod
    def render(path: str, params: dict):
        template = get_template(path)
        html = template.render(params)
        response = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), response)
        if not pdf.err:
            return HttpResponse(response.getvalue(), content_type='application/pdf')
        else:
            return HttpResponse("Error Rendering PDF", status=400)


"""
function for viewing allocations from NOIC, showing sord numbers, quantities, payment etc

"""


@login_required
@user_role
def sord_allocations(request):
    sord_allocations = SordCompanyAuditTrail.objects.filter(company=request.user.company).all()
    today = date.today().strftime("%d/%m/%y")
    
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
            sord_allocations = SordCompanyAuditTrail.objects.filter(company=request.user.company, date__range=[start_date, end_date])
        
            return render(request, 'users/sord_allocations.html', {'sord_allocations': sord_allocations, 'start_date':start_date, 'end_date': end_date })
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
                sord_allocations = SordCompanyAuditTrail.objects.filter(company=request.user.company, date__range=[start_date, end_date])

            fields = ['date', 'sord_no', 'action_no', 'action', 'fuel_type', 'payment_type', 'initial_quantity', 'quantity_allocated', 'end_quantity']
            sord_allocations = sord_allocations.values('date', 'sord_no', 'action_no', 'action', 'fuel_type', 'payment_type', 'initial_quantity', 'quantity_allocated', 'end_quantity')            
            df = pd.DataFrame(sord_allocations, columns=fields)
            filename = 'Supplier Admin'

            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - Sord AuditTrails- {today}.csv'
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
                sord_allocations = SordCompanyAuditTrail.objects.filter(company=request.user.company, date__range=[start_date, end_date])   
            html_string = render_to_string('users/export_allocations.html', {'sord_allocations': sord_allocations, 'date':today })
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} - {today}.pdf'
                return response
            

    
    return render(request, 'users/sord_allocations.html', {'sord_allocations': sord_allocations})


"""
functions for allocating fuel to depots and stations

"""


@login_required()
@user_role
def allocate(request):
    allocates = []
    fuel_object = DepotFuelUpdate.objects.first()
    diesel_rtgs_price = 0
    diesel_usd_price = 0
    petrol_rtgs_price = 0
    petrol_usd_price = 0
    if fuel_object is not None:
        diesel_rtgs_price = fuel_object.rtgs_diesel_price
        diesel_usd_price = fuel_object.usd_diesel_price
        petrol_rtgs_price = fuel_object.rtgs_petrol_price
        petrol_usd_price = fuel_object.usd_petrol_price
    form1 = DepotContactForm()
    notifications = Notification.objects.filter(action="FOR_FUEL").filter(is_read=False).all()
    num_of_notifications = Notification.objects.filter(action="FOR_FUEL").filter(is_read=False).count()
    depots = NoicDepot.objects.filter(is_active=True).all()
    form1.fields['depot'].choices = [((depot.id, depot.name)) for depot in depots]
    company_capacity = CompanyFuelUpdate.objects.filter(company=request.user.company).first()
    subs_total_diesel_capacity = 0
    subs_total_petrol_capacity = 0
    subsidiaries_fuel = SubsidiaryFuelUpdate.objects.filter(subsidiary__company=request.user.company).all()
    for sub_fuel in subsidiaries_fuel:
        subs_total_diesel_capacity += sub_fuel.diesel_quantity
        subs_total_petrol_capacity += sub_fuel.petrol_quantity

    company_total_diesel_capacity = subs_total_diesel_capacity + company_capacity.unallocated_diesel
    company_total_petrol_capacity = subs_total_petrol_capacity + company_capacity.unallocated_petrol

    # company_total_diesel_capacity = '{:,}'.format(company_total_diesel_capacity)
    # company_total_petrol_capacity = '{:,}'.format(company_total_petrol_capacity)

    subs = Subsidiaries.objects.filter(company=request.user.company, is_active=True).all()
    for sub in subs:
        allocates.append(SubsidiaryFuelUpdate.objects.filter(subsidiary=sub).first())
    allocations = FuelAllocation.objects.filter(company=request.user.company).all()
    # if company_capacity is not None:
    #     company_capacity.unallocated_diesel = '{:,}'.format(company_capacity.unallocated_diesel)
    #     company_capacity.unallocated_petrol = '{:,}'.format(company_capacity.unallocated_petrol)
    # else:
    #     company_capacity = company_capacity
    if allocations is not None:
        for alloc in allocations:
            subsidiary = Subsidiaries.objects.filter(id=alloc.allocated_subsidiary_id).first()
            if subsidiary is not None:
                alloc.subsidiary_name = subsidiary.name
            else:
                allocations = allocations
    else:
        allocations = allocations
    return render(request, 'users/allocate.html',
                  {'notifications': notifications, 'num_of_notifications': num_of_notifications, 'depots': depots, 'form1': form1, 'diesel_rtgs_price': diesel_rtgs_price,
                   'diesel_usd_price': diesel_usd_price, 'petrol_rtgs_price': petrol_rtgs_price,
                   'petrol_usd_price': petrol_usd_price, 'allocates': allocates, 'allocations': allocations,
                   'company_capacity': company_capacity,
                   'company_total_diesel_capacity': company_total_diesel_capacity,
                   'company_total_petrol_capacity': company_total_petrol_capacity})


@login_required()
def allocated_fuel(request, sid):
    user_permission(request)
    prices = FuelPrices.objects.first()
    sub = Subsidiaries.objects.filter(id=sid).first()
    allocates = SuballocationFuelUpdate.objects.filter(subsidiary=sub).all()
    company_quantity = CompanyFuelUpdate.objects.filter(company=request.user.company).first()
    depot = SubsidiaryFuelUpdate.objects.filter(subsidiary=sub).first()

    if request.method == 'POST':
        if request.POST['fuel_type'] == 'Petrol':
            if int(request.POST['quantity']) > company_quantity.unallocated_petrol:
                messages.warning(request, f'You can not allocate fuel above your company petrol capacity of {company_quantity.unallocated_petrol}.')
                return redirect(f'/users/allocated_fuel/{sid}')
            if request.POST['fuel_payment_type'] == "RTGS":
                if Decimal(request.POST['price']) > prices.rtgs_petrol_price:
                    messages.warning(request, f'You can not set price above ZERA max petrol price of ${prices.rtgs_petrol_price}.')
                    return redirect(f'/users/allocated_fuel/{sid}')
                else:
                    pass
            elif request.POST['fuel_payment_type'] == "USD":
                if Decimal(request.POST['price']) > prices.usd_petrol_price:
                    messages.warning(request, f'You can not set price above ZERA max petrol price of ${prices.usd_petrol_price}')
                    return redirect(f'/users/allocated_fuel/{sid}')
                else:
                    pass
            fuel_updated = SuballocationFuelUpdate.objects.create(subsidiary=sub,
                                                                  payment_type=request.POST['fuel_payment_type'],
                                                                  cash=request.POST['cash'],
                                                                  swipe=request.POST['swipe'],
                                                                  petrol_quantity=request.POST['quantity'],
                                                                  petrol_price=request.POST['price'])
            if request.POST['fuel_payment_type'] == 'USD & RTGS':
                fuel_updated.petrol_usd_price = request.POST['usd_price']
                fuel_updated.ecocash = request.POST['ecocash']
            elif request.POST['fuel_payment_type'] == 'RTGS':
                fuel_updated.ecocash = request.POST['ecocash']
            else:
                pass
            depot.petrol_quantity = depot.petrol_quantity + int(request.POST['quantity'])
            company_quantity.unallocated_petrol = company_quantity.unallocated_petrol - int(request.POST['quantity'])
            company_quantity.save()
            messages.success(request, 'Fuel Allocation SUccesful')
            return redirect(f'/users/allocated_fuel/{sid}')
        else:
            if int(request.POST['quantity']) > company_quantity.unallocated_diesel:
                messages.warning(request,
                                 f'You can not allocate fuel above your company diesel capacity of {company_quantity.unallocated_diesel}.')
                return redirect(f'/users/allocated_fuel/{sid}')
            if request.POST['fuel_payment_type'] == "RTGS":
                if Decimal(request.POST['price']) > prices.rtgs_diesel_price:
                    messages.warning(request, f'You can not set price above ZERA max diesel price of ${prices.rtgs_diesel_price}.')
                    return redirect(f'/users/allocated_fuel/{sid}')
                else:
                    pass
            elif request.POST['fuel_payment_type'] == "USD":
                if Decimal(request.POST['price']) > prices.usd_diesel_price:
                    messages.warning(request, f'You can not set price above ZERA max diesel price of ${prices.usd_diesel_price}.')
                    return redirect(f'/users/allocated_fuel/{sid}')
                else:
                    pass
            fuel_updated = SuballocationFuelUpdate.objects.create(subsidiary=sub,
                                                                  payment_type=request.POST['fuel_payment_type'],
                                                                  cash=request.POST['cash'],
                                                                  swipe=request.POST['swipe'],
                                                                  diesel_quantity=request.POST['quantity'],
                                                                  diesel_price=request.POST['price'])
            if request.POST['fuel_payment_type'] == 'USD & RTGS':
                fuel_updated.diesel_usd_price = request.POST['usd_price']
                fuel_updated.ecocash = request.POST['ecocash']
            elif request.POST['fuel_payment_type'] == 'RTGS':
                fuel_updated.ecocash = request.POST['ecocash']
            else:
                pass
            depot.diesel_quantity = depot.diesel_quantity + int(request.POST['quantity'])
            company_quantity.unallocated_diesel = company_quantity.unallocated_diesel - int(request.POST['quantity'])
            company_quantity.save()
            messages.success(request, 'Fuel allocation succesfull.')
        fuel_updated.save()
        depot.save()

        action = 'Allocation of ' + request.POST['fuel_type']
        if request.POST['fuel_type'].lower() == 'petrol':
            FuelAllocation.objects.create(company=request.user.company, fuel_payment_type=fuel_updated.payment_type,
                                          action=action, petrol_price=fuel_updated.petrol_price,
                                          petrol_quantity=request.POST['quantity'], sub_type="Suballocation",
                                          cash=request.POST['cash'], swipe=request.POST['swipe'],
                                          allocated_subsidiary_id=fuel_updated.subsidiary.id)
            proceed = True
            amount_cf = float(request.POST['quantity'])

            while proceed:
                sord_allocation = SordCompanyAuditTrail.objects.filter(company=request.user.company, fuel_type="Petrol",
                                                                       payment_type=fuel_updated.payment_type).filter(~Q(end_quantity=0)).first()
                if sord_allocation.end_quantity >= amount_cf:
                    sord_allocation.quantity_allocated += amount_cf
                    sord_allocation.end_quantity -= amount_cf
                    sord_allocation.action_no += 1
                    sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                    sord_allocation.save()
                    proceed = False
                    action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                        action_num=sord_allocation.action_no,
                                                                        allocated_quantity=amount_cf,
                                                                        action_type="Allocation",
                                                                        supplied_from=request.user.company.name,
                                                                        price=fuel_updated.petrol_price,
                                                                        allocated_by=request.user.username,
                                                                        allocated_to=sub.name, fuel_type="Petrol",
                                                                        payment_type=fuel_updated.payment_type)
                    receiver = User.objects.filter(subsidiary_id=sub.id).first()
                    depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                          sord_no=sord_allocation.sord_no,
                                                                          action_no=sord_allocation.action_no,
                                                                          action="Receiving Fuel", fuel_type="Petrol",
                                                                          payment_type=fuel_updated.payment_type,
                                                                          initial_quantity=amount_cf,
                                                                          end_quantity=amount_cf, received_by=receiver)
                    depot_audit.save()
                else:
                    amount_cf -= sord_allocation.end_quantity
                    sord_allocation.end_quantity = 0
                    sord_allocation.quantity_allocated += sord_allocation.end_quantity
                    sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                    sord_allocation.action_no += 1
                    sord_allocation.save()
                    action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                        action_num=sord_allocation.action_no,
                                                                        allocated_quantity=sord_allocation.end_quantity,
                                                                        allocated_by=request.user.username,
                                                                        action_type="Allocation",
                                                                        price=fuel_updated.petrol_price,
                                                                        supplied_from=request.user.company.name,
                                                                        allocated_to=sub.name, fuel_type="Petrol",
                                                                        payment_type=fuel_updated.payment_type)
                    receiver = User.objects.filter(subsidiary_id=sub.id).first()
                    depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                          sord_no=sord_allocation.sord_no,
                                                                          action_no=sord_allocation.action_no,
                                                                          action="Receiving Fuel", fuel_type="Petrol",
                                                                          payment_type=fuel_updated.payment_type,
                                                                          initial_quantity=sord_allocation.end_quantity,
                                                                          end_quantity=sord_allocation.end_quantity,
                                                                          received_by=receiver)
                    depot_audit.save()
        else:
            FuelAllocation.objects.create(company=request.user.company, fuel_payment_type=fuel_updated.payment_type,
                                          action=action, diesel_price=fuel_updated.diesel_price,
                                          diesel_quantity=request.POST['quantity'], sub_type="Suballocation",
                                          cash=request.POST['cash'], swipe=request.POST['swipe'],
                                          allocated_subsidiary_id=fuel_updated.subsidiary.id)
            proceed = True
            amount_cf = float(request.POST['quantity'])

            while proceed:
                sord_allocation = SordCompanyAuditTrail.objects.filter(company=request.user.company, fuel_type="Diesel",
                                                                       payment_type=fuel_updated.payment_type).filter(~Q(end_quantity=0)).first()
                if sord_allocation.end_quantity >= amount_cf:
                    sord_allocation.quantity_allocated += amount_cf
                    sord_allocation.end_quantity -= amount_cf
                    sord_allocation.action_no += 1
                    sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                    sord_allocation.save()
                    proceed = False
                    action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                        action_num=sord_allocation.action_no,
                                                                        allocated_quantity=amount_cf,
                                                                        allocated_by=request.user.username,
                                                                        action_type="Allocation",
                                                                        price=fuel_updated.diesel_price,
                                                                        supplied_from=request.user.company.name,
                                                                        allocated_to=sub.name, fuel_type="Diesel",
                                                                        payment_type=fuel_updated.payment_type)
                    receiver = User.objects.filter(subsidiary_id=sub.id).first()
                    depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                          sord_no=sord_allocation.sord_no,
                                                                          action_no=sord_allocation.action_no,
                                                                          action="Receiving Fuel", fuel_type="Diesel",
                                                                          payment_type=fuel_updated.payment_type,
                                                                          initial_quantity=amount_cf,
                                                                          end_quantity=amount_cf, received_by=receiver)
                    depot_audit.save()
                else:
                    amount_cf -= sord_allocation.end_quantity
                    sord_allocation.end_quantity = 0
                    sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                    sord_allocation.quantity_allocated += sord_allocation.end_quantity
                    sord_allocation.action_no += 1
                    sord_allocation.save()
                    action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                        action_num=sord_allocation.action_no,
                                                                        allocated_quantity=sord_allocation.end_quantity,
                                                                        allocated_by=request.user.username,
                                                                        action_type="Allocation",
                                                                        price=fuel_updated.diesel_price,
                                                                        supplied_from=request.user.company.name,
                                                                        allocated_to=sub.name, fuel_type="Diesel",
                                                                        payment_type=fuel_updated.payment_type)
                    receiver = User.objects.filter(subsidiary_id=sub.id).first()
                    depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                          sord_no=sord_allocation.sord_no,
                                                                          action_no=sord_allocation.action_no,
                                                                          action="Receiving Fuel", fuel_type="Diesel",
                                                                          payment_type=fuel_updated.payment_type,
                                                                          initial_quantity=sord_allocation.end_quantity,
                                                                          end_quantity=sord_allocation.end_quantity,
                                                                          received_by=receiver)
                    depot_audit.save()

    type_list = []
    if allocates is not None:

        for allocate in allocates:
            type_list.append(allocate.payment_type)
            subsidiary = Subsidiaries.objects.filter(id=allocate.subsidiary.id).first()
            if subsidiary is not None:
                allocate.subsidiary_name = subsidiary.name
                
            else:
                allocates = allocates
        else:
            allocates = allocates
    return render(request, 'users/fuel_allocations.html', {'allocates': allocates, 'type_list': type_list})


@login_required()
def allocation_update(request, id):
    user_permission(request)
    prices = FuelPrices.objects.first()
    if request.method == 'POST':
        if SuballocationFuelUpdate.objects.filter(id=id).exists():
            fuel_update = SuballocationFuelUpdate.objects.filter(id=id).first()
            sub = Subsidiaries.objects.filter(id=fuel_update.subsidiary.id).first()
            company_quantity = CompanyFuelUpdate.objects.filter(company=request.user.company).first()
            depot = SubsidiaryFuelUpdate.objects.filter(subsidiary=sub).first()
            if request.POST['fuel_type'] == 'Petrol':
                if int(request.POST['quantity']) > company_quantity.unallocated_petrol:
                    messages.warning(request, f'You can not allocate fuel above your company petrol quantity of {company_quantity.unallocated_petrol}.')
                    return redirect('users:allocate')
                fuel_update.petrol_quantity = fuel_update.petrol_quantity + int(request.POST['quantity'])
                depot.petrol_quantity = depot.petrol_quantity + int(request.POST['quantity'])
                if fuel_update.payment_type == "RTGS":
                    if Decimal(request.POST['price']) > prices.rtgs_petrol_price:
                        messages.warning(request, f'You can not set price above ZERA max petrol price of ${prices.rtgs_petrol_price}.')
                        return redirect(f'/users/allocated_fuel/{fuel_update.subsidiary.id}')
                    else:
                        fuel_update.petrol_price = Decimal(request.POST['price'])
                elif fuel_update.payment_type == "USD":
                    if Decimal(request.POST['price']) > prices.usd_petrol_price:
                        messages.warning(request, f'You can not set price above ZERA max usd petrol price of ${prices.usd_petrol_price}.')
                        return redirect(f'/users/allocated_fuel/{fuel_update.subsidiary.id}')
                    else:
                        fuel_update.petrol_price = Decimal(request.POST['price'])
                if fuel_update.payment_type == 'USD & RTGS':
                    fuel_update.petrol_usd_price = Decimal(request.POST['usd_price'])
                company_quantity.unallocated_petrol = company_quantity.unallocated_petrol - int(request.POST['quantity'])
                company_quantity.save()
            else:
                if int(request.POST['quantity']) > company_quantity.unallocated_diesel:
                    messages.warning(request, f'You can not allocate fuel above your company diesel quantity of {company_quantity.unallocated_diesel}.')
                    return redirect(f'/users/allocated_fuel/{fuel_update.subsidiary.id}')
                fuel_update.diesel_quantity = fuel_update.diesel_quantity + int(request.POST['quantity'])
                depot.diesel_quantity = depot.diesel_quantity + int(request.POST['quantity'])

                if fuel_update.payment_type == "RTGS":
                    if Decimal(request.POST['price']) > prices.rtgs_diesel_price:
                        messages.warning(request, f'You can not set price above ZERA max diesel price of ${prices.rtgs_diesel_price}.')
                        return redirect(f'/users/allocated_fuel/{fuel_update.subsidiary.id}')
                    else:
                        fuel_update.diesel_price = Decimal(request.POST['price'])
                elif fuel_update.payment_type == "USD":
                    if Decimal(request.POST['price']) > prices.usd_diesel_price:
                        messages.warning(request, f'You can not set price above ZERA max usd diesel price of ${prices.usd_diesel_price}.')
                        return redirect(f'/users/allocated_fuel/{fuel_update.subsidiary.id}')
                    else:
                        fuel_update.diesel_price = Decimal(request.POST['price'])
                if fuel_update.payment_type == 'USD & RTGS':
                    fuel_update.diesel_usd_price = float(request.POST['usd_price'])
                company_quantity.unallocated_diesel = company_quantity.unallocated_diesel - int(request.POST['quantity'])
                company_quantity.save()
            fuel_update.cash = request.POST['cash']
            fuel_update.swipe = request.POST['swipe']
            if fuel_update.payment_type != 'USD':
                fuel_update.ecocash = request.POST['ecocash']

            fuel_update.save()
            depot.save()

            action = 'Allocation of ' + request.POST['fuel_type']
            if request.POST['fuel_type'].lower() == 'petrol':
                FuelAllocation.objects.create(company=request.user.company, fuel_payment_type=fuel_update.payment_type,
                                              action=action, petrol_price=fuel_update.petrol_price,
                                              petrol_quantity=request.POST['quantity'], sub_type="Suballocation",
                                              cash=request.POST['cash'], swipe=request.POST['swipe'],
                                              allocated_subsidiary_id=fuel_update.subsidiary.id)
                proceed = True
                amount_cf = float(request.POST['quantity'])

                while proceed:
                    sord_allocation = SordCompanyAuditTrail.objects.filter(company=request.user.company,
                                                                           fuel_type="Petrol",
                                                                           payment_type=fuel_update.payment_type).filter(~Q(end_quantity=0)).first()
                    if sord_allocation:
                        if sord_allocation.end_quantity >= amount_cf:
                            sord_allocation.quantity_allocated += amount_cf
                            sord_allocation.end_quantity -= amount_cf
                            sord_allocation.action_no += 1
                            sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                            sord_allocation.save()
                            proceed = False
                            action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                                action_num=sord_allocation.action_no,
                                                                                allocated_quantity=amount_cf,
                                                                                allocated_by=request.user.username,
                                                                                action_type="Allocation",
                                                                                price=fuel_update.petrol_price,
                                                                                supplied_from=request.user.company.name,
                                                                                allocated_to=sub.name, fuel_type="Petrol",
                                                                                payment_type=fuel_update.payment_type)
                            receiver = User.objects.filter(subsidiary_id=sub.id).first()
                            depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                                sord_no=sord_allocation.sord_no,
                                                                                action_no=sord_allocation.action_no,
                                                                                action="Receiving Fuel",
                                                                                fuel_type="Petrol",
                                                                                payment_type=fuel_update.payment_type,
                                                                                initial_quantity=amount_cf,
                                                                                end_quantity=amount_cf,
                                                                                received_by=receiver)
                            depot_audit.save()
                        else:
                            amount_cf -= sord_allocation.end_quantity
                            sord_allocation.end_quantity = 0
                            sord_allocation.quantity_allocated += sord_allocation.end_quantity
                            sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                            sord_allocation.action_no += 1
                            sord_allocation.save()
                            action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                                action_num=sord_allocation.action_no,
                                                                                allocated_quantity=sord_allocation.end_quantity,
                                                                                allocated_by=request.user.username,
                                                                                action_type="Allocation",
                                                                                price=fuel_update.petrol_price,
                                                                                supplied_from=request.user.company.name,
                                                                                allocated_to=sub.name, fuel_type="Petrol",
                                                                                payment_type=fuel_update.payment_type)
                            receiver = User.objects.filter(subsidiary_id=sub.id).first()
                            depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                                sord_no=sord_allocation.sord_no,
                                                                                action_no=sord_allocation.action_no,
                                                                                action="Receiving Fuel",
                                                                                fuel_type="Petrol",
                                                                                payment_type=fuel_update.payment_type,
                                                                                initial_quantity=sord_allocation.end_quantity,
                                                                                end_quantity=sord_allocation.end_quantity,
                                                                                received_by=receiver)
                            depot_audit.save()
                    else:
                        messages.warning(request, 'Sord not found.')
                        return redirect(f'/users/allocated_fuel/{fuel_update.subsidiary.id}')

            else:
                FuelAllocation.objects.create(company=request.user.company, fuel_payment_type=fuel_update.payment_type,
                                              action=action, diesel_price=fuel_update.diesel_price,
                                              diesel_quantity=request.POST['quantity'], sub_type="Suballocation",
                                              cash=request.POST['cash'], swipe=request.POST['swipe'],
                                              allocated_subsidiary_id=fuel_update.subsidiary.id)
                proceed = True
                amount_cf = float(request.POST['quantity'])

                while proceed:
                    sord_allocation = SordCompanyAuditTrail.objects.filter(company=request.user.company,
                                                                           fuel_type="Diesel",
                                                                           payment_type=fuel_update.payment_type).filter(~Q(end_quantity=0)).first()
                    if sord_allocation.end_quantity >= amount_cf:
                        sord_allocation.quantity_allocated += amount_cf
                        sord_allocation.end_quantity -= amount_cf
                        sord_allocation.action_no += 1
                        sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                        sord_allocation.save()
                        proceed = False
                        action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                            action_num=sord_allocation.action_no,
                                                                            allocated_quantity=amount_cf,
                                                                            allocated_by=request.user.username,
                                                                            action_type="Allocation",
                                                                            price=fuel_update.diesel_price,
                                                                            supplied_from=request.user.company.name,
                                                                            allocated_to=sub.name, fuel_type="Diesel",
                                                                            payment_type=fuel_update.payment_type)
                        receiver = User.objects.filter(subsidiary_id=sub.id).first()
                        depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                              sord_no=sord_allocation.sord_no,
                                                                              action_no=sord_allocation.action_no,
                                                                              action="Receiving Fuel",
                                                                              fuel_type="Diesel",
                                                                              payment_type=fuel_update.payment_type,
                                                                              initial_quantity=amount_cf,
                                                                              end_quantity=amount_cf,
                                                                              received_by=receiver)
                        depot_audit.save()
                    else:
                        amount_cf -= sord_allocation.end_quantity
                        sord_allocation.end_quantity = 0
                        sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                        sord_allocation.quantity_allocated += sord_allocation.end_quantity
                        sord_allocation.action_no += 1
                        sord_allocation.save()
                        action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                            action_num=sord_allocation.action_no,
                                                                            allocated_quantity=sord_allocation.end_quantity,
                                                                            allocated_by=request.user.username,
                                                                            action_type="Allocation",
                                                                            price=fuel_update.diesel_price,
                                                                            supplied_from=request.user.company.name,
                                                                            allocated_to=sub.name, fuel_type="Diesel",
                                                                            payment_type=fuel_update.payment_type)
                        receiver = User.objects.filter(subsidiary_id=sub.id).first()
                        depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                              sord_no=sord_allocation.sord_no,
                                                                              action_no=sord_allocation.action_no,
                                                                              action="Receiving Fuel",
                                                                              fuel_type="Diesel",
                                                                              payment_type=fuel_update.payment_type,
                                                                              initial_quantity=sord_allocation.end_quantity,
                                                                              end_quantity=sord_allocation.end_quantity,
                                                                              received_by=receiver)
                        depot_audit.save()

            messages.success(request, 'Fuel allocation successfull.')
            service_station = Subsidiaries.objects.filter(id=fuel_update.subsidiary.id).first()
            reference = 'fuel allocation'
            reference_id = fuel_update.id
            action = f"You have allocated {request.POST['fuel_type']} quantity of {int(request.POST['quantity'])}L @ {fuel_update.petrol_price}. "
            Audit_Trail.objects.create(company=request.user.company, service_station=service_station, user=request.user,
                                       action=action, reference=reference, reference_id=reference_id)
            return redirect(f'/users/allocated_fuel/{fuel_update.subsidiary.id}')

        else:
            messages.success(request, 'Subsidiary does not exists.')
            return redirect('users:allocate')
    return render(request, 'users/allocate.html')


@login_required()
def allocation_update_main(request, id):
    user_permission(request)
    prices = FuelPrices.objects.first()
    if request.method == 'POST':
        if SubsidiaryFuelUpdate.objects.filter(id=id).exists():
            fuel_update = SubsidiaryFuelUpdate.objects.filter(id=id).first()
            sub = Subsidiaries.objects.filter(id=fuel_update.subsidiary.id).first()
            company_quantity = CompanyFuelUpdate.objects.filter(company=request.user.company).first()

            if request.POST['fuel_type'] == 'Petrol':
                if int(request.POST['quantity']) > company_quantity.unallocated_petrol:
                    messages.warning(request, f'You can not allocate fuel above your company petrol quantity of {company_quantity.unallocated_petrol}.')
                    return redirect(f'/users/allocated_fuel/{fuel_update.subsidiary.id}')
                fuel_update.petrol_quantity = fuel_update.petrol_quantity + int(request.POST['quantity'])
                if Decimal(request.POST['price']) > prices.rtgs_petrol_price:
                    messages.warning(request, f'You can not set price above ZERA max petrol price of ${prices.rtgs_petrol_price}.')
                    return redirect(f'/users/allocated_fuel/{fuel_update.subsidiary.id}')
                else:
                    fuel_update.petrol_price = Decimal(request.POST['price'])
                company_quantity.unallocated_petrol = company_quantity.unallocated_petrol - int(
                    request.POST['quantity'])
                company_quantity.save()
            else:
                if int(request.POST['quantity']) > company_quantity.unallocated_diesel:
                    messages.warning(request, f'You can not allocate fuel above your company diesel quantity of {company_quantity.unallocated_diesel}.')
                    return redirect(f'/users/allocated_fuel/{fuel_update.subsidiary.id}')
                fuel_update.diesel_quantity = fuel_update.diesel_quantity + int(request.POST['quantity'])
                if Decimal(request.POST['price']) > prices.rtgs_diesel_price:
                    messages.warning(request, f'You can not set price above ZERA max diesel price of ${prices.rtgs_diesel_price}.')
                    return redirect(f'/users/allocated_fuel/{fuel_update.subsidiary.id}')
                else:
                    fuel_update.diesel_price = Decimal(request.POST['price'])
                company_quantity.unallocated_diesel = company_quantity.unallocated_diesel - int(
                    request.POST['quantity'])
                company_quantity.save()
            fuel_update.cash = request.POST['cash']
            fuel_update.swipe = request.POST['swipe']
            fuel_update.ecocash = request.POST['ecocash']

            fuel_update.save()

            action = 'Allocation of ' + request.POST['fuel_type']
            if request.POST['fuel_type'].lower() == 'petrol':
                FuelAllocation.objects.create(company=request.user.company, fuel_payment_type="RTGS", action=action,
                                              petrol_price=fuel_update.petrol_price,
                                              petrol_quantity=request.POST['quantity'], sub_type="Service Station",
                                              cash=request.POST['cash'], swipe=request.POST['swipe'],
                                              allocated_subsidiary_id=fuel_update.subsidiary.id)
                proceed = True
                amount_cf = float(request.POST['quantity'])

                while proceed:
                    sord_allocation = SordCompanyAuditTrail.objects.filter(company=request.user.company,
                                                                           fuel_type="Petrol", payment_type="RTGS").filter(~Q(end_quantity=0)).first()
                    if sord_allocation:    
                        if sord_allocation.end_quantity >= amount_cf:
                            sord_allocation.quantity_allocated += amount_cf
                            sord_allocation.end_quantity -= amount_cf
                            sord_allocation.action_no += 1
                            sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                            sord_allocation.save()
                            proceed = False
                            action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                                action_num=sord_allocation.action_no,
                                                                                allocated_quantity=amount_cf,
                                                                                allocated_by=request.user.username,
                                                                                action_type="Allocation",
                                                                                price=fuel_update.petrol_price,
                                                                                supplied_from=request.user.company.name,
                                                                                allocated_to=sub.name, fuel_type="Petrol",
                                                                                payment_type="RTGS")
                            receiver = User.objects.filter(subsidiary_id=sub.id).first()
                            depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                                sord_no=sord_allocation.sord_no,
                                                                                action_no=sord_allocation.action_no,
                                                                                action="Receiving Fuel",
                                                                                fuel_type="Petrol", payment_type="RTGS",
                                                                                initial_quantity=amount_cf,
                                                                                end_quantity=amount_cf,
                                                                                received_by=receiver)
                            depot_audit.save()
                        else:
                            amount_cf -= sord_allocation.end_quantity
                            sord_allocation.end_quantity = 0
                            sord_allocation.quantity_allocated += sord_allocation.end_quantity
                            sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                            sord_allocation.action_no += 1
                            sord_allocation.save()
                            action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                                action_num=sord_allocation.action_no,
                                                                                allocated_quantity=sord_allocation.end_quantity,
                                                                                allocated_by=request.user.username,
                                                                                action_type="Allocation",
                                                                                price=fuel_update.petrol_price,
                                                                                supplied_from=request.user.company.name,
                                                                                allocated_to=sub.name, fuel_type="Petrol",
                                                                                payment_type="RTGS")
                            receiver = User.objects.filter(subsidiary_id=sub.id).first()
                            depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                                sord_no=sord_allocation.sord_no,
                                                                                action_no=sord_allocation.action_no,
                                                                                action="Receiving Fuel",
                                                                                fuel_type="Petrol", payment_type="RTGS",
                                                                                initial_quantity=sord_allocation.end_quantity,
                                                                                end_quantity=sord_allocation.end_quantity,
                                                                                received_by=receiver)
                            depot_audit.save()

                    else:
                        messages.warning(request, 'Sord not found.')
                        return redirect('users:allocate')
                          
            else:
                FuelAllocation.objects.create(company=request.user.company, fuel_payment_type="RTGS", action=action,
                                              diesel_price=fuel_update.diesel_price,
                                              diesel_quantity=request.POST['quantity'], sub_type="Service Station",
                                              cash=request.POST['cash'], swipe=request.POST['swipe'],
                                              allocated_subsidiary_id=fuel_update.subsidiary.id)
                proceed = True
                amount_cf = float(request.POST['quantity'])

                while proceed:
                    sord_allocation = SordCompanyAuditTrail.objects.filter(company=request.user.company,
                                                                           fuel_type="Diesel", payment_type="RTGS").filter(~Q(end_quantity=0)).first()
                    if sord_allocation.end_quantity >= amount_cf:
                        sord_allocation.quantity_allocated += amount_cf
                        sord_allocation.end_quantity -= amount_cf
                        sord_allocation.action_no += 1
                        sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                        sord_allocation.save()
                        proceed = False
                        action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                            action_num=sord_allocation.action_no,
                                                                            allocated_quantity=amount_cf,
                                                                            allocated_by=request.user.username,
                                                                            action_type="Allocation",
                                                                            price=fuel_update.diesel_price,
                                                                            supplied_from=request.user.company.name,
                                                                            allocated_to=sub.name, fuel_type="Diesel",
                                                                            payment_type="RTGS")
                        receiver = User.objects.filter(subsidiary_id=sub.id).first()
                        depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                              sord_no=sord_allocation.sord_no,
                                                                              action_no=sord_allocation.action_no,
                                                                              action="Receiving Fuel",
                                                                              fuel_type="Diesel", payment_type="RTGS",
                                                                              initial_quantity=amount_cf,
                                                                              end_quantity=amount_cf,
                                                                              received_by=receiver)
                        depot_audit.save()
                    else:
                        amount_cf -= sord_allocation.end_quantity
                        sord_allocation.end_quantity = 0
                        sord_allocation.action = f'Allocation of {request.POST["fuel_type"]}'
                        sord_allocation.quantity_allocated += sord_allocation.end_quantity
                        sord_allocation.action_no += 1
                        sord_allocation.save()
                        action_audit = SordActionsAuditTrail.objects.create(sord_num=sord_allocation.sord_no,
                                                                            action_num=sord_allocation.action_no,
                                                                            allocated_quantity=sord_allocation.end_quantity,
                                                                            allocated_by=request.user.username,
                                                                            action_type="Allocation",
                                                                            price=fuel_update.diesel_price,
                                                                            supplied_from=request.user.company.name,
                                                                            allocated_to=sub.name, fuel_type="Diesel",
                                                                            payment_type="RTGS")
                        receiver = User.objects.filter(subsidiary_id=sub.id).first()
                        depot_audit = SordSubsidiaryAuditTrail.objects.create(subsidiary=sub,
                                                                              sord_no=sord_allocation.sord_no,
                                                                              action_no=sord_allocation.action_no,
                                                                              action="Receiving Fuel",
                                                                              fuel_type="Diesel", payment_type="RTGS",
                                                                              initial_quantity=sord_allocation.end_quantity,
                                                                              end_quantity=sord_allocation.end_quantity,
                                                                              received_by=receiver)
                        depot_audit.save()

            messages.success(request, 'Fuel allocation successfull.')
            service_station = Subsidiaries.objects.filter(id=fuel_update.subsidiary.id).first()
            reference = 'sfuel allocation'
            reference_id = fuel_update.id
            action = f"You have allocated {request.POST['fuel_type']} quantity of {int(request.POST['quantity'])}L @ {fuel_update.petrol_price} "
            Audit_Trail.objects.create(company=request.user.company, service_station=service_station, user=request.user,
                                       action=action, reference=reference, reference_id=reference_id)
            return redirect('users:allocate')

        else:
            messages.success(request, 'Subsidiary does not exists.')
            return redirect('users:allocate')
    return render(request, 'users/allocate.html')


"""
function for creating subsidiaries (Depots & Stations) & their fuel update objects

"""


@login_required()
@user_role
def stations(request):
    stations = Subsidiaries.objects.filter(company=request.user.company).all()
    zimbabwean_towns = ['Select City ---', 'Beitbridge', 'Bindura', 'Bulawayo', 'Chinhoyi', 'Chirundu', 'Gweru',
                        'Harare',
                        'Hwange', 'Juliusdale', 'Kadoma', 'Kariba', 'Karoi', 'Kwekwe', 'Marondera', 'Masvingo',
                        'Mutare',
                        'Mutoko', 'Nyanga', 'Victoria Falls']
    Harare = ['Avenues', 'Budiriro', 'Dzivaresekwa', 'Kuwadzana', 'Warren Park', 'Glen Norah', 'Glen View', 'Avondale',
              'Belgravia', 'Belvedere', 'Eastlea', 'Gun Hill', 'Milton Park', 'Borrowdale', 'Chisipiti', 'Glen Lorne',
              'Greendale', 'Greystone Park', 'Helensvale', 'Highlands', 'Mandara', 'Manresa', 'Msasa', 'Newlands',
              'The Grange', 'Ashdown Park', 'Avonlea', 'Bluff Hill', 'Borrowdale', 'Emerald Hill', 'Greencroft',
              'Hatcliffe', 'Mabelreign', 'Marlborough', 'Meyrick Park', 'Mount Pleasant', 'Pomona', 'Tynwald',
              'Vainona', 'Arcadia', 'Braeside', 'CBD', 'Cranbourne', 'Graniteside', 'Hillside', 'Queensdale',
              'Sunningdale', 'Epworth', 'Highfield' 'Kambuzuma', 'Southerton', 'Warren Park', 'Southerton', 'Mabvuku',
              'Tafara', 'Mbare', 'Prospect', 'Ardbennie', 'Houghton Park', 'Marimba Park', 'Mufakose']
    Bulawayo = ['New Luveve', 'Newsmansford', 'Newton', 'Newton West', 'Nguboyenja', 'Njube', 'Nketa', 'Nkulumane',
                'North End', 'Northvale', 'North Lynne', 'Northlea', 'North Trenance', 'Ntaba Moyo', 'Ascot',
                'Barbour Fields', 'Barham Green', 'Beacon Hill', 'Belmont Industrial area', 'Bellevue', 'Belmont',
                'Bradfield']
    Mutare = ['Murambi', 'Hillside', 'Fairbridge Park', 'Morningside', 'Tigers Kloof', 'Yeovil', 'Westlea', 'Florida',
              'Chikanga', 'Garikai', 'Sakubva', 'Dangamvura', 'Weirmouth', 'Fern Valley', 'Palmerstone', 'Avenues',
              'Utopia', 'Darlington', 'Greeside', 'Greenside Extension', 'Toronto', 'Bordervale', 'Natview Park',
              'Mai Maria', 'Gimboki', 'Musha Mukadzi']
    Gweru = ['Gweru East', 'Woodlands Park', 'Kopje', 'Mtausi Park', 'Nashville', 'Senga', 'Hertifordshire', 'Athlone',
             'Daylesford', 'Mkoba', 'Riverside', 'Southview', 'Nehosho', 'Clydesdale Park', 'Lundi Park', 'Montrose',
             'Ascot', 'Ridgemont', 'Windsor Park', 'Ivene', 'Haben Park', 'Bata', 'ThornHill Air Field' 'Green Dale',
             'Bristle', 'Southdowns']
    form1 = SupplierContactForm()
    form = DepotContactForm()
    if request.method == 'POST':
        name = request.POST['name']
        city = request.POST['city']
        location = request.POST['location']
        destination_bank = request.POST['destination_bank']
        account_number = request.POST['account_number']
        praz_reg_num = request.POST['praz']
        vat = request.POST['vat']
        if request.POST['is_depot'] == "Service Station":
            is_depot = False
        else:
            is_depot = True
        opening_time = request.POST['opening_time']
        closing_time = request.POST['closing_time']
        if request.POST['new'] == "New":
            application_form = request.FILES.get('application_form')
            fire_brigade = request.FILES.get('fire_brigade')
            ema = request.FILES.get('ema')
            is_active = False
            license_num = None
        else:
            is_active = True
            license_num = request.POST['licence']
            application_form = None
            fire_brigade = None
            ema = None

        subsidiary = Subsidiaries.objects.create(is_active=is_active, application_form=application_form,
                                                 fire_brigade=fire_brigade, ema=ema, license_num=license_num,
                                                 praz_reg_num=praz_reg_num,
                                                 vat=vat, account_number=account_number,
                                                 destination_bank=destination_bank, city=city, location=location,
                                                 company=request.user.company, name=name, is_depot=is_depot,
                                                 opening_time=opening_time, closing_time=closing_time)
        subsidiary.save()
        if request.POST['is_depot'] == "Service Station":
            fuel_update = SubsidiaryFuelUpdate.objects.create(subsidiary=subsidiary,
                                                              limit=2000)
            fuel_update.save()
            messages.success(request, 'Subsidiary created successfully.')
            message = 'Registering new subsdiary'
            Notification.objects.create(handler_id=5, message=message, reference_id=subsidiary.id, responsible_subsidiary=subsidiary, action="NEW_SUBSIDIARY")
            return render(request, 'users/service_stations.html',
                          {'stations': stations, 'Harare': Harare, 'Bulawayo': Bulawayo,
                           'zimbabwean_towns': zimbabwean_towns,
                           'Mutare': Mutare, 'Gweru': Gweru, 'subsidiary': subsidiary, 'form': form, 'form1': form1,
                           'add_user': 'show'})

        else:
            fuel_update = SubsidiaryFuelUpdate.objects.create(subsidiary=subsidiary,
                                                              limit=2000)
            fuel_update.save()
            messages.success(request, 'Subsidiary created successfully.')
            message = 'Registering new subsdiary'
            Notification.objects.create(handler_id=5, message=message, reference_id=subsidiary.id, responsible_subsidiary=subsidiary, action="NEW_SUBSIDIARY")
            return render(request, 'users/service_stations.html',
                          {'stations': stations, 'Harare': Harare, 'Bulawayo': Bulawayo,
                           'zimbabwean_towns': zimbabwean_towns,
                           'Mutare': Mutare, 'Gweru': Gweru, 'subsidiary': subsidiary, 'form': form, 'form1': form1,
                           'add_user': 'show'})

    return render(request, 'users/service_stations.html',
                  {'stations': stations, 'Harare': Harare, 'Bulawayo': Bulawayo, 'zimbabwean_towns': zimbabwean_towns,
                   'Mutare': Mutare, 'Gweru': Gweru, 'add_user': 'hide', 'allocate': 'hide'})


@login_required()
@user_role
def suppliers_list(request):
    suppliers = User.objects.filter(company=request.user.company).filter(~Q(user_type='S_ADMIN')).all()
    stations = Subsidiaries.objects.filter(is_depot=False).filter(company=request.user.company).all()
    depots = Subsidiaries.objects.filter(is_depot=True).filter(company=request.user.company).all()
    applicants = User.objects.filter(is_waiting=True, company=request.user.company).all()
    if suppliers is not None:
        for supplier in suppliers:
            subsidiary = Subsidiaries.objects.filter(id=supplier.subsidiary_id).first()
            if subsidiary is not None:
                supplier.subsidiary = subsidiary
            else:
                pass
    else:
        suppliers = None
    form1 = SupplierContactForm()
    form = DepotContactForm()

    subsidiaries = Subsidiaries.objects.filter(is_depot=False).filter(is_active=True).filter(
        company=request.user.company).all()
    depots = Subsidiaries.objects.filter(is_depot=True).filter(is_active=True).filter(
        company=request.user.company).all()
    form1.fields['service_station'].choices = [((subsidiary.id, subsidiary.name)) for subsidiary in subsidiaries]
    form.fields['depot'].choices = [((subsidiary.id, subsidiary.name)) for subsidiary in depots]

    if request.method == 'POST':
        form1 = SupplierContactForm(request.POST)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = random_password()
        phone_number = request.POST.get('phone_number')
        subsidiary_id = request.POST.get('service_station')
        full_name = first_name + " " + last_name
        i = 0
        username = initial_username = first_name[0] + last_name
        while User.objects.filter(username=username.lower()).exists():
            username = initial_username + str(i)
            i += 1

        sup = User.objects.filter(email=email).first()
        if sup is not None:
            messages.warning(request, f"The email {sup.email} already used in the system, please use a different email.")
            return redirect('users:suppliers_list')

        user = User.objects.create(company_position='manager', subsidiary_id=subsidiary_id, username=username.lower(),
                                   first_name=first_name, last_name=last_name,
                                   company=request.user.company, email=email,
                                   phone_number=phone_number, password_reset=True)
        subsidiary = Subsidiaries.objects.filter(id=subsidiary_id).first()
        if subsidiary.is_depot == False:
            user.user_type = 'SS_SUPPLIER'
            user.save()
            fuel_update = SubsidiaryFuelUpdate.objects.filter(subsidiary=subsidiary).first()
            user.set_password(password)
            if message_is_send(request, user, password):
                if user.is_active:
                    user.stage = 'menu'
                    user.save()
                else:
                    messages.warning(request, f"Oops , something went wrong, please try again")
            return render(request, 'users/suppliers_list.html',
                          {'suppliers': suppliers, 'form1': form1, 'allocate': 'show', 'fuel_update': fuel_update,
                           'form': form})
        else:
            user.user_type = 'SUPPLIER'
            user.save()
            user.set_password(password)
            if message_is_send(request, user, password):
                if user.is_active:
                    user.stage = 'menu'
                    user.save()
                else:
                    messages.warning(request, f"Oops , something went wrong, please try again")
            return redirect(f'/users/allocated_fuel/{subsidiary.id}')

    return render(request, 'users/suppliers_list.html', {'suppliers': suppliers, 'form1': form1, 'form': form,
                                                        'applicants': applicants, 'stations': stations, 'depots': depots})


@login_required()
@user_role
def get_pdf(request):
    trans = Transaction.objects.all()
    today = datetime.datetime.today()
    params = {
        'today': today,
        'trans': trans,
        'request': request
    }
    return Render.render('users/pdf.html', params)


@login_required()
@user_role
def account_activate(request):
    return render(request, 'users/account_activate.html')


@login_required()
@user_role
def index(request):
    return render(request, 'users/index.html')


@login_required
@user_role
def delivery_schedule(request):
    pass


@login_required()
@user_role
def statistics(request):
    company = request.user.company
    yesterday = date.today() - timedelta(days=1)
    monthly_rev = get_monthly_sales(request.user.company, datetime.now().year)
    weekly_rev = get_weekly_sales(request.user.company, True)
    last_week_rev = get_weekly_sales(request.user.company, False)
    last_year_rev = get_monthly_sales(request.user.company, (datetime.now().year - 1))
    # offers = Offer.objects.filter(supplier__company=request.user.company).count()
    # bulk_requests = FuelRequest.objects.filter(delivery_method="SELF COLLECTION").count()
    # normal_requests = FuelRequest.objects.filter(delivery_method="DELIVERY").count()  # Change these 2 items
    # staff = ''
    # new_orders = FuelRequest.objects.filter(date__gt=yesterday).count()
    # try:
    #     rating = SupplierRating.objects.filter(supplier=request.user.company).first().rating
    # except:
    #     rating = 0

    # admin_staff = User.objects.filter(company=company).filter(user_type='SUPPLIER').count()
    # # all_staff = User.objects.filter(company=company).count()
    # other_staff = User.objects.filter(company=company).filter(user_type='SS_SUPPLIER').count()
    clients = []
    # stock = get_aggregate_stock(request.user.company)
    # diesel = stock['diesel']
    # petrol = stock['petrol']

    trans = Transaction.objects.filter(supplier__company=request.user.company, is_complete=True).annotate(
        number_of_trans=Count('buyer')).order_by('-number_of_trans')[:10]
    buyers = [client.buyer for client in trans]

    branches = Subsidiaries.objects.filter(is_depot=True).filter(company=request.user.company)

    subs = []

    for sub in branches:
        tran_amount = 0
        sub_trans = Transaction.objects.filter(supplier__company=request.user.company, supplier__subsidiary_id=sub.id,
                                               is_complete=True)
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
        buyers.remove(buyer)
        new_buyer_transactions = Transaction.objects.filter(buyer=buyer, supplier__company=request.user.company,
                                                            is_complete=True).all()
        total_value = 0
        purchases = []
        number_of_trans = 0
        for tran in new_buyer_transactions:
            total_value += (float(tran.offer.request.amount) * float(tran.offer.price))
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
    revenue = get_total_revenue(request.user)
    revenue = '${:,.2f}'.format(revenue)
    # revenue = str(revenue) + '.00'

    # try:
    #     trans = Transaction.objects.filter(supplier=request.user, complete=true).count()/Transaction.objects.all().count()/100
    # except:
    #     trans = 0    
    trans_complete = get_transactions_complete_percentage(request.user)
    average_rating = get_average_rating(request.user.company)
    return render(request, 'users/statistics.html', {'trans': trans, 'clients': clients,
                                                     'sorted_subs': sorted_subs,
                                                     'monthly_rev': monthly_rev, 'weekly_rev': weekly_rev,
                                                     'last_week_rev': last_week_rev})


@login_required()
def supplier_user_edit(request, cid):
    user_permission(request)
    supplier = User.objects.filter(id=cid).first()

    if request.method == "POST":
        # supplier.company = request.POST['company']
        supplier.phone_number = request.POST['phone_number']
        supplier.supplier_role = request.POST['user_type']
        # supplier.supplier_role = request.POST['supplier_role']
        supplier.save()
        messages.success(request, 'Your changes have been saved.')
    return render(request, 'users/suppliers_list.html')


@login_required
def client_history(request, cid):
    user_permission(request)
    buyer = User.objects.filter(id=cid).first()
    trans = []
    state = 'All'

    if request.method == "POST":

        if request.POST.get('report_type') == 'Completed':
            trns = Transaction.objects.filter(buyer=buyer, is_complete=True)
            trans = []
            for tran in trns:
                tran.revenue = tran.offer.request.amount * tran.offer.price
                tran.account_history = AccountHistory.objects.filter(transaction=tran).all()
                trans.append(tran)
            state = 'Complete'

        if request.POST.get('report_type') == 'Incomplete':
            trns = Transaction.objects.filter(buyer=buyer, is_complete=False)
            trans = []
            for tran in trns:
                tran.revenue = Decimal(tran.offer.request.amount) * tran.offer.price
                tran.account_history = AccountHistory.objects.filter(transaction=tran).all()
                trans.append(tran)
            state = 'Incomplete'

        if request.POST.get('report_type') == 'All':
            trns = Transaction.objects.filter(buyer=buyer)
            trans = []
            for tran in trns:
                tran.revenue = Decimal(tran.offer.request.amount) * tran.offer.price
                tran.account_history = AccountHistory.objects.filter(transaction=tran).all()
                trans.append(tran)
            state = 'All'

        return render(request, 'users/client_history.html', {'trans': trans, 'buyer': buyer, 'state': state})

    trns = Transaction.objects.filter(buyer=buyer)
    trans = []
    for tran in trns:
        tran.revenue = tran.offer.request.amount * tran.offer.price
        tran.account_history = AccountHistory.objects.filter(transaction=tran).all()
        trans.append(tran)

    return render(request, 'users/client_history.html', {'trans': trans, 'buyer': buyer, 'state': state})


@login_required
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
                tran.revenue = tran.offer.request.amount * tran.offer.price
                tran.account_history = AccountHistory.objects.filter(transaction=tran).all()
                trans.append(tran)
            state = 'Complete'

        if request.POST.get('report_type') == 'Incomplete':
            trns = Transaction.objects.filter(supplier__subsidiary_id=subsidiary.id, is_complete=False)
            trans = []
            for tran in trns:
                tran.revenue = tran.offer.request.amount * tran.offer.price
                tran.account_history = AccountHistory.objects.filter(transaction=tran).all()
                trans.append(tran)
            state = 'Incomplete'

        if request.POST.get('report_type') == 'All':
            trns = Transaction.objects.filter(supplier__subsidiary_id=subsidiary.id)
            trans = []
            for tran in trns:
                tran.revenue = tran.offer.request.amount * tran.offer.price
                tran.account_history = AccountHistory.objects.filter(transaction=tran).all()
                trans.append(tran)
            state = 'All'
        return render(request, 'users/subs_history.html', {'trans': trans, 'subsidiary': subsidiary, 'state': state})

    trns = Transaction.objects.filter(supplier__subsidiary_id=subsidiary.id)
    for tran in trns:
        tran.revenue = tran.offer.request.amount * tran.offer.price
        tran.account_history = AccountHistory.objects.filter(transaction=tran).all()
        trans.append(tran)

    return render(request, 'users/subs_history.html', {'trans': trans, 'subsidiary': subsidiary})


@login_required()
@user_role
def myaccount(request):
    staff = user.objects.get(id=request.user.id)
    if request.method == 'POST':
        staff.email = request.POST['email']
        staff.phone_number = request.POST['phone_number']
        staff.company_position = request.POST['company_position']
        staff.save()
        messages.success(request, 'Your changes have been saved.')

    return render(request, 'users/profile.html')


@login_required()
@user_role
def report_generator(request):
    '''View to dynamically render form tables based on different criteria'''
    form = ReportForm()
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
        if request.POST.get('report_type') == 'Transactions' or request.POST.get('report_type') == 'Revenue':
            trans = Transaction.objects.filter(date__range=[start_date, end_date],
                                               supplier__company=request.user.company)
            requests = None
            allocations = None
            revs = None

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
            trans = None
            allocations = None
            stock = None
            revs = None
        if request.POST.get('report_type') == 'Allocations':
            allocations = SordCompanyAuditTrail.objects.filter(company=request.user.company, date__range=[start_date, end_date])
            requests = None
            revs = None
            stock = None
        start = start_date
        end = end_date

        # revs = 0
        return render(request, 'users/reports.html',
                      {'trans': trans, 'requests': requests, 'allocations': allocations, 'form': form,
                       'start': start, 'end': end, 'revs': revs, 'stock': stock})

    show = False
    return render(request, 'users/reports.html',
                  {'trans': trans, 'requests': requests, 'allocations': allocations, 'form': form,
                   'start': start_date, 'end': end_date, 'show': show, 'stock': stock})


@login_required()
@user_role
def depots(request):
    depots = Depot.objects.all()
    return render(request, 'users/depots.html', {'depots': depots})


@login_required()
@user_role
def audit_trail(request):
    filtered = False
    filtered_trails = None
    trails = Audit_Trail.objects.exclude(date__gt=today).filter(company=request.user.company)
    for activity in trails:
        if activity.reference == 'offers':
            activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'sfuel allocation':
            activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'fuel allocation':
            activity.fuel_update = SuballocationFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'sprices updates':
            activity.prices_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'prices updates':
            activity.prices_update = SuballocationFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'pfuel quantity updates':
            activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'dfuel quantity updates':
            activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()

    current_trails = Audit_Trail.objects.filter(company=request.user.company, date__gt=today).all()
    for activity in current_trails:
        if activity.reference == 'offers':
            activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'sfuel allocation':
            activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'fuel allocation':
            activity.fuel_update = SuballocationFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'sprices updates':
            activity.prices_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'prices updates':
            activity.prices_update = SuballocationFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'pfuel quantity updates':
            activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
        elif activity.reference == 'dfuel quantity updates':
            activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()

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
            
            filtered_trails = Audit_Trail.objects.filter(company=request.user.company).filter(date__date__range=[start_date, end_date])
            return render(request, 'users/audit_trail.html', {'filtered_trails':filtered_trails,'filtered':filtered ,'today':today, 'start_date': start_date
            , 'end_date':end_date})

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
                filtered_trails = Audit_Trail.objects.filter(company=request.user.company).filter(date__date__range=[start_date, end_date])
                   
            if filtered_trails:  
                for activity in filtered_trails:
                    if activity.reference == 'offers':
                        activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'sfuel allocation':
                        activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'fuel allocation':
                        activity.fuel_update = SuballocationFuelUpdate.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'sprices updates':
                        activity.prices_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'prices updates':
                        activity.prices_update = SuballocationFuelUpdate.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'pfuel quantity updates':
                        activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'dfuel quantity updates':
                        activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()

            fields = ['date','user__company__name', 'service_station__name', 'action', 'reference',]
            
            if filtered_trails:
                filtered_trails = filtered_trails.values('date','user__company__name', 'service_station__name', 'action', 'reference')
                df = pd.DataFrame(filtered_trails, columns=fields)
            else:
                df_current = pd.DataFrame(current_trails.values('date','user__company__name', 'service_station__name', 'action', 'reference'), columns=fields)
                df_previous = pd.DataFrame(trails.values('date','user__company__name', 'service_station__name', 'action', 'reference'), columns=fields)
                df = df_current.append(df_previous)

            filename = f'{request.user.company.name}'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - AuditTrail- {today}.csv'
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
                filtered_trails = Audit_Trail.objects.filter(company=request.user.company).filter(date__date__range=[start_date, end_date])

            if filtered_trails:
                for activity in filtered_trails:
                    if activity.reference == 'offers':
                        activity.offer_object = Offer.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'sfuel allocation':
                        activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'fuel allocation':
                        activity.fuel_update = SuballocationFuelUpdate.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'sprices updates':
                        activity.prices_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'prices updates':
                        activity.prices_update = SuballocationFuelUpdate.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'pfuel quantity updates':
                        activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()
                    elif activity.reference == 'dfuel quantity updates':
                        activity.fuel_update = SubsidiaryFuelUpdate.objects.filter(id=activity.reference_id).first()

            html_string = render_to_string('users/export/export_activity.html', {'filtered_trails': filtered_trails,'filtered': filtered,'date':today, 'start_date':start_date
            ,'trails': trails, 'current_trails':current_trails, 'end_date':end_date})
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} -Orders - {today}.pdf'
                return response 
                
    


    return render(request, 'users/audit_trail.html', {'trails': trails,'filtered': filtered, 'current_trails': current_trails, 'today':today})


@login_required()
@user_role
def approve_applicant(request, id):
    user_permission(request)
    if request.method == 'POST':
        if user.objects.filter(id=id).exists():
            applicant = user.objects.filter(id=id).first()
            applicant.is_waiting = False
            applicant.is_active = True
            selected_id = request.POST['subsidiary']
            selected_subsidiary = Subsidiaries.objects.filter(id=selected_id).first()
            applicant.subsidiary_id = selected_subsidiary.id
            applicant.save()
            messages.success(request, f'{applicant.first_name.title()} has been approved successfully.')
            return redirect('users:waiting_for_approval')

        else:
            messages.warning(request, 'Oops, something went wrong.')
            return redirect('users:waiting_for_approval')


@login_required()
def decline_applicant(request, id):
    user_permission(request)
    applicant = user.objects.filter(id=id).first()
    applicant.delete()
    messages.warning(request, f'declined a request for registration from {applicant.first_name}')
    return redirect('users:waiting_for_approval')


@login_required()
def message_is_send(request, user, password):
    user_permission(request)
    sender = "intelliwhatsappbanking@gmail.com"
    subject = 'ZFMS Registration'
    message = f"Dear {user.first_name}  {user.last_name}. \nYour Username is: {user.username}\nYour Initial Password is: {password} \n\nPlease login on ZFMS Website and access your assigned Station & don't forget to change your password on user profile. \n. "
    try:
        msg = EmailMultiAlternatives(subject, message, sender, [f'{user.email}'])
        msg.send()
        messages.success(request, f"{user.first_name}  {user.last_name} Registered successfully")
        return True
    except Exception as e:
        messages.warning(request,
                         f"Oops , something went wrong while sending email. Please make sure you have internet access.")
        return False
    return render(request, 'buyer/send_email.html')


# @login_required()
def message_is_sent(request, user, password):
    # user_permission(request)
    sender = "intelliwhatsappbanking@gmail.com"
    subject = 'ZFMS Registration'
    message = f"Dear {user.first_name}  {user.last_name}. \nYour Username is: {user.username}\nYour Initial Password is: {password} \n\nPlease download the ZFMS mobile app on PlayStore and login to start looking for fuel. \n. "
    try:
        msg = EmailMultiAlternatives(subject, message, sender, [f'{user.email}'])
        msg.send()
        # messages.success(request, f"{user.first_name}  {user.last_name} Registered Successfully")
        return True
    except Exception as e:
        # messages.warning(request, f"Oops , Something Wen't Wrong sending email, Please make sure you have Internet access")
        return False



@login_required()
def suppliers_delete(request, sid):
    user_permission(request)
    supplier = User.objects.filter(id=sid).first()
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, f"{supplier.username.title()} deleted successfully")
        return redirect('users:suppliers_list')
    else:
        messages.success(request, 'User does not exists.')
        return redirect('users:suppliers_list')


# DO NOT DELETE DEPOT STAFF MANAGEMENT VIEWS!!!!!!!!!!!
@login_required()
def delete_depot_staff(request, id):
    user_permission(request)
    supplier = User.objects.filter(id=id).first()
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, f"{supplier.username} deleted successfully")
        return redirect('users:suppliers_list')
    else:
        messages.success(request, 'User does not exists.')
        return redirect('users:suppliers_list')


@login_required()
@user_role
def buyers_list(request):
    buyers = Profile.objects.all()
    edit_form = ProfileEditForm()
    delete_form = ActionForm()
    return render(request, 'users/buyers_list.html',
                  {'buyers': buyers, 'edit_form': edit_form, 'delete_form': delete_form})


@login_required()
def buyers_delete(request, sid):
    user_permission(request)
    buyer = Profile.objects.filter(id=sid).first()
    if request.method == 'POST':
        buyer.delete()

    return redirect('users:buyers_list')


@login_required()
def supplier_user_delete(request, cid, sid):
    user_permission(request)
    contact = SupplierContact.objects.filter(id=cid).first()
    if request.method == 'POST':
        contact.delete()

    return redirect('users:supplier_user_create', sid=sid)


@login_required()
def supplier_user_create(request, sid):
    user_permission(request)
    return render(request, 'users/suppliers_list.html')


@login_required()
def buyer_user_create(request, sid):
    user_permission(request)
    return render(request, 'users/add_buyer.html')


@login_required()
def edit_buyer(request, id):
    user_permission(request)
    return render(request, 'users/buyer_edit.html', {'form': form, 'buyer': buyer})


@login_required()
def delete_user(request, id):
    user_permission(request)
    supplier = get_object_or_404(Profile, id=id)

    if request.method == 'POST':
        form = ActionForm(request.POST)
        if form.is_valid():
            supplier.delete()
            messages.success(request, 'User has been deleted.')
        return redirect('administrator:blog_all_posts')
    form = ActionForm()

    return render(request, 'users/supplier_delete.html', {'form': form, 'supplier': supplier})


@login_required()
def depot_staff(request):
    user_permission(request)
    suppliers = User.objects.filter(company=request.user.company).filter(user_type='SUPPLIER').all()
    for supplier in suppliers:
        subsidiary = Subsidiaries.objects.filter(id=supplier.subsidiary_id).first()
        if subsidiary:
            supplier.subsidiary_name = subsidiary.name
    # suppliers = [sup for sup in suppliers if not sup == request.user]
    form1 = DepotContactForm()
    subsidiaries = Subsidiaries.objects.filter(is_depot=True).filter(company=request.user.company).all()
    form1.fields['depot'].choices = [((subsidiary.id, subsidiary.name)) for subsidiary in subsidiaries]

    if request.method == 'POST':

        form1 = DepotContactForm(request.POST)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        sup = User.objects.filter(email=email).first()
        if sup is not None:
            messages.warning(request, f"The emai {sup.email} is already being used in the system, please use a different email.")
            return redirect('users:suppliers_list')

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
                                   first_name=first_name, last_name=last_name, user_type='SUPPLIER',
                                   company=request.user.company, email=email,
                                   phone_number=phone_number, password_reset=True)
        user.set_password(password)
        if message_is_send(request, user, password):
            if user.is_active:
                # messages.success(request, "You have been registered succesfully")
                user.stage = 'menu'
                user.save()

                # return render(request, 'buyer/email_send.html')
            else:
                messages.warning(request, f"Oops , something went wrong. Please try again.")
                # return render(request, 'buyer/email_send.html')
        # messages.success(request, f"{username.lower()} Registered as Depot Rep Successfully")
        return redirect('users:suppliers_list')
    '''
    else:
        messages.warning(request, f"The username has already been,please use another username to register")
        return redirect('users:depot_staff')
    '''

    return render(request, 'users/depot_staff.html', {'suppliers': suppliers, 'form1': form1})


'''
Password Change Functions
'''

@login_required
@user_role
def initial_password_change(request):
    if request.method == 'POST':
        password1 = request.POST['new_password1']
        password2 = request.POST['new_password2']
        if password1 != password2:
            messages.warning(request, "Passwords don't match.")
            return redirect('users:initial-password-change')
        elif len(password1) < 8:
            messages.warning(request, "Password is too short.")
            return redirect('users:initial-password-change')
        elif password1.isnumeric():
            messages.warning(request, "Password can not be entirely numeric.")
            return redirect('users:initial-password-change')
        elif not password1.isalnum():
            messages.warning(request, "Password should be alphanumeric.")
            return redirect('users:initial-password-change')
        else:
            user = request.user
            user.set_password(password1)
            user.password_reset = False
            user.save()
            update_session_auth_hash(request, user)

            messages.success(request, 'Password successfully changed.')
            return redirect('users:allocate')
    return render(request, 'users/initial_pass_change.html')


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
                return redirect('users:change-password')
            elif new1 == old:
                messages.warning(request, "New password can not be similar to the old one.")
                return redirect('users:change-password')
            elif len(new1) < 8:
                messages.warning(request, "Password is too short.")
                return redirect('users:change-password')
            elif new1.isnumeric():
                messages.warning(request, "Password can not be entirely numeric.")
                return redirect('users:change-password')
            elif not new1.isalnum():
                messages.warning(request, "Password should be alphanumeric.")
                return redirect('users:change-password')
            else:
                user = request.user
                user.set_password(new1)
                user.save()
                update_session_auth_hash(request, user)

                messages.success(request, 'Password successfully changed.')
                return redirect('users:myaccount')
        else:
            messages.warning(request, 'Wrong old password, please try again.')
            return redirect('users:change-password')
    return render(request, 'users/change_password.html', context=context)


@login_required()
def edit_subsidiary(request, id):
    user_permission(request)
    if request.method == 'POST':
        if Subsidiaries.objects.filter(id=id).exists():
            subsidiary_update = Subsidiaries.objects.filter(id=id).first()
            subsidiary_update.name = request.POST['name']
            subsidiary_update.location = request.POST['address']
            subsidiary_update.is_depot = request.POST['is_depot']
            subsidiary_update.opening_time = request.POST['opening_time']
            subsidiary_update.closing_time = request.POST['closing_time']
            subsidiary_update.save()
            messages.success(request, 'Subsidiary updated successfully.')
            reference = 'subsidiary profile update'
            reference_id = subsidiary_update.id
            action = f"You have updated the profile of {subsidiary_update.name}"
            Audit_Trail.objects.create(company=request.user.company, service_station=subsidiary_update,
                                       user=request.user, action=action, reference=reference, reference_id=reference_id)
            return redirect('users:stations')
        else:
            messages.success(request, 'Subsidiary does not exists.')
            return redirect('users:stations')


@login_required()
def delete_subsidiary(request, id):
    user_permission(request)
    if request.method == 'POST':
        if Subsidiaries.objects.filter(id=id).exists():
            subsidiary_update = Subsidiaries.objects.filter(id=id).first()
            subsidiary_update.delete()
            messages.success(request, 'Subsidiary deleted successfully.')
            return redirect('users:stations')

        else:
            messages.success(request, 'Subsidiary does not exists.')
            return redirect('users:stations')


@login_required()
def edit_fuel_prices(request, id):
    user_permission(request)
    prices = FuelPrices.objects.first()
    if request.method == 'POST':
        if SubsidiaryFuelUpdate.objects.filter(id=id).exists():
            prices_update = SubsidiaryFuelUpdate.objects.filter(id=id).first()
            company_capacity = CompanyFuelUpdate.objects.filter(company=request.user.company).first()
            if Decimal(request.POST['petrol_price']) > prices.rtgs_petrol_price:
                messages.warning(request, f'You can not set price above ZERA max petrol price of ${prices.rtgs_petrol_price}.')
                return redirect('users:allocate')
            prices_update.petrol_price = Decimal(request.POST['petrol_price'])

            if Decimal(request.POST['diesel_price']) > prices.rtgs_diesel_price:
                messages.warning(request,  f'You can not set price above ZERA max diesel price of ${prices.rtgs_diesel_price}.')
                return redirect('users:allocate')
            prices_update.diesel_price = Decimal(request.POST['diesel_price'])
            prices_update.save()
            messages.success(request, 'Prices of fuel updated successfully.')
            service_station = Subsidiaries.objects.filter(id=prices_update.subsidiary.id).first()
            reference = 'sprices updates'
            reference_id = prices_update.id
            action = f"You have changed petrol price to {request.POST['petrol_price']} and diesel price to {request.POST['diesel_price']} "
            Audit_Trail.objects.create(company=request.user.company, service_station=service_station, user=request.user,
                                       action=action, reference=reference, reference_id=reference_id)
            return redirect('users:allocate')

        else:
            messages.success(request, 'Fuel object does not exists.')
            return redirect('users:allocate')


@login_required()
def edit_suballocation_fuel_prices(request, id):
    user_permission(request)
    prices = FuelPrices.objects.first()
    if request.method == 'POST':
        if SuballocationFuelUpdate.objects.filter(id=id).exists():
            prices_update = SuballocationFuelUpdate.objects.filter(id=id).first()
            company_capacity = CompanyFuelUpdate.objects.filter(company=request.user.company).first()
            if Decimal(request.POST['petrol_price']) > prices.rtgs_petrol_price:
                messages.warning(request, f'You can not set price above ZERA max petrol price of ${prices.rtgs_petrol_price}.')
                return redirect(f'/users/allocated_fuel/{prices_update.subsidiary.id}')
            prices_update.petrol_price = Decimal(request.POST['petrol_price'])
            if Decimal(request.POST['diesel_price']) > prices.rtgs_diesel_price:
                messages.warning(request, f'You can not set price above ZERA max diesel price of ${prices.rtgs_diesel_price}.')
                return redirect(f'/users/allocated_fuel/{prices_update.subsidiary.id}')
            prices_update.diesel_price = Decimal(request.POST['diesel_price'])
            prices_update.save()
            messages.success(request, 'Prices of fuel updated successfully.')
            service_station = Subsidiaries.objects.filter(id=prices_update.subsidiary.id).first()
            reference = 'prices updates'
            reference_id = prices_update.id
            action = f"You have changed petrol price to {request.POST['petrol_price']} and diesel price to {request.POST['diesel_price']} "
            Audit_Trail.objects.create(company=request.user.company, service_station=service_station, user=request.user,
                                       action=action, reference=reference, reference_id=reference_id)
            return redirect(f'/users/allocated_fuel/{prices_update.subsidiary.id}')

        else:
            messages.success(request, 'Fuel object does not exists.')
            return redirect('users:allocate')


@login_required()
def edit_ss_rep(request, id):
    user_permission(request)
    if request.method == 'POST':
        if user.objects.filter(id=id).exists():
            user_update = user.objects.filter(id=id).first()
            user_update.first_name = request.POST['first_name']
            user_update.last_name = request.POST['last_name']
            user_update.email = request.POST['email']
            user_update.phone_number = request.POST['phone_number']
            user_update.save()
            messages.success(request, 'User profile updated successfully')
            return redirect('users:suppliers_list')

        else:
            messages.success(request, 'User does not exists.')
            return redirect('users:suppliers_list')


@login_required()
def edit_depot_rep(request, id):
    user_permission(request)
    if request.method == 'POST':
        if user.objects.filter(id=id).exists():
            user_update = user.objects.filter(id=id).first()
            user_update.first_name = request.POST['first_name']
            user_update.last_name = request.POST['last_name']
            user_update.email = request.POST['email']
            user_update.phone_number = request.POST['phone_number']
            user_update.save()
            messages.success(request, 'User profile updated successfully.')
            return redirect('users:suppliers_list')

        else:
            messages.success(request, 'User does not exists.')
            return redirect('users:suppliers_list')


@login_required()
@user_role
def company_profile(request):
    compan = Company.objects.filter(id=request.user.company.id).first()
    num_of_subsidiaries = Subsidiaries.objects.filter(company=request.user.company).count()
    # fuel_capacity = CompanyFuelUpdate.objects.filter(company=request.user.company).first()

    if request.method == 'POST':
        compan.name = request.POST['name']
        compan.address = request.POST['address']
        compan.industry = request.POST['industry']
        compan.iban_number = request.POST['iban_number']
        compan.licence_number = request.POST['licence_number']
        compan.destination_bank = request.POST['destination_bank']
        compan.account_number = request.POST['account_number']
        compan.save()
        messages.success(request, 'Company profile updated successfully.')
        return redirect('users:company_profile')

    return render(request, 'users/company_profile.html', {'compan': compan, 'num_of_subsidiaries': num_of_subsidiaries})


@login_required()
def company_petrol(request, id):
    user_permission(request)
    if request.method == 'POST':
        if CompanyFuelUpdate.objects.filter(id=id).exists():
            petrol_update = CompanyFuelUpdate.objects.filter(id=id).first()
            petrol_update.petrol_price = request.POST['petrol_price']
            petrol_update.unallocated_petrol = request.POST['petrol_quantity']
            petrol_update.save()
            messages.success(request, 'Quantity of petrol updated successfully.')
            return redirect('users:allocate')

        else:
            messages.success(request, 'Fuel object does not exists.')
            return redirect('users:allocate')


@login_required()
def company_diesel(request, id):
    user_permission(request)
    if request.method == 'POST':
        if CompanyFuelUpdate.objects.filter(id=id).exists():
            diesel_update = CompanyFuelUpdate.objects.filter(id=id).first()
            diesel_update.unallocated_diesel = request.POST['diesel_quantity']
            diesel_update.diesel_price = request.POST['diesel_price']
            diesel_update.save()
            messages.success(request, 'Quantity of diesel updated successfully.')
            return redirect('users:allocate')

        else:
            messages.warning(request, 'Fuel object does not exists.')
            return redirect('users:allocate')


@login_required()
def edit_allocation(request, id):
    user_permission(request)
    if request.method == 'POST':
        if FuelAllocation.objects.filter(id=id).exists():
            correction = FuelAllocation.objects.filter(id=id).first()
            if int(request.POST['diesel_quantity']) > 0:
                sub = Subsidiaries.objects.filter(id=correction.allocated_subsidiary_id).first()
                updated = SubsidiaryFuelUpdate.objects.filter(subsidiary=sub).first()
                updated.diesel_quantity = int(updated.diesel_quantity) - int(
                    int(correction.diesel_quantity) - int(request.POST['diesel_quantity']))
                updated.save()
                company_fuel = CompanyFuelUpdate.objects.filter(company=request.user.company).first()
                if int(request.POST['diesel_quantity']) > int(company_fuel.unallocated_diesel):
                    messages.warning(request,
                                     'You can not edit an allocation to an amount greater than the company unallocated diesel quantity. ')
                    return redirect('users:allocate')
                company_fuel.unallocated_diesel = int(company_fuel.unallocated_diesel) + int(
                    int(correction.diesel_quantity) - int(request.POST['diesel_quantity']))
                company_fuel.save()
                correction.diesel_quantity = request.POST['diesel_quantity']
                correction.save()
            else:
                sub = Subsidiaries.objects.filter(id=correction.allocated_subsidiary_id).first()
                updated = SubsidiaryFuelUpdate.objects.filter(subsidiary=sub).first()
                updated.petrol_quantity = int(updated.petrol_quantity) - int(
                    int(correction.petrol_quantity) - int(request.POST['petrol_quantity']))
                updated.save()
                company_fuel = CompanyFuelUpdate.objects.filter(company=request.user.company).first()
                if int(request.POST['petrol_quantity']) > int(company_fuel.unallocated_petrol):
                    messages.warning(request,
                                     'You can not edit an allocation to an amount greater than the company unallocated petrol quantity. ')
                    return redirect('users:allocate')
                company_fuel.unallocated_petrol = int(company_fuel.unallocated_petrol) + int(
                    int(correction.petrol_quantity) - int(request.POST['petrol_quantity']))
                company_fuel.save()
                correction.petrol_quantity = request.POST['petrol_quantity']
                correction.save()
            messages.success(request, 'Quantity of fuel corrected successfully.')
            return redirect('users:allocate')

        else:
            messages.warning(request, 'Fuel object does not exists.')
            return redirect('users:allocate')


@login_required()
def sordactions(request, sid):
    user_permission(request)
    sord_actions = SordActionsAuditTrail.objects.filter(sord_num=sid).all()

    if sord_actions:
        sord_number = sord_actions[0].sord_num
    else:
        sord_number = "-"
    return render(request, 'users/sord_actions.html', {'sord_number': sord_number, 'sord_actions': sord_actions})


@login_required()
@user_role
def sord_station_sales(request):
    sord_sales = SordSubsidiaryAuditTrail.objects.filter(subsidiary__company=request.user.company)
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
            sord_sales = SordSubsidiaryAuditTrail.objects.filter(subsidiary__company=request.user.company, date__range=[start_date, end_date])
        
            return render(request, 'users/sord_station_sales.html', {'sord_sales': sord_sales, 'start_date':start_date, 'end_date':end_date })
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
                sord_sales = SordSubsidiaryAuditTrail.objects.filter(subsidiary__company=request.user.company, date__range=[start_date, end_date])

            fields = ['date','subsidiary__name','sord_no', 'action_no', 'action', 'fuel_type', 'payment_type', 'initial_quantity', 'quantity_sold', 'end_quantity']
            df = pd.DataFrame(sord_sales.values('date','subsidiary__name','sord_no', 'action_no', 'action', 'fuel_type', 'payment_type', 'initial_quantity', 'quantity_sold', 'end_quantity'),
            columns=fields)
            filename = 'Supplier Admin'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - Sord Sales- {today}.csv'
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
                sord_sales = SordSubsidiaryAuditTrail.objects.filter(subsidiary__company=request.user.company, date__range=[start_date, end_date])   
            html_string = render_to_string('users/export/export_station_sales.html', {'sord_sales': sord_sales, 'date':today, 'start_date':start_date, 'end_date':end_date})
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} - {today}.pdf'
                return response

    return render(request, 'users/sord_station_sales.html', {'sord_sales': sord_sales})


@login_required()
@user_role
def delivery_schedule(request, id):
    user_permission(request)
    return render(request, 'users/delivery_schedule.html')


@login_required
@user_role
def clients(request):
    context = {
        'clients': Account.objects.filter(is_verified=False, supplier_company=request.user.company).all(),
        'form': UsersUploadForm(),
        'accounts': Account.objects.filter(supplier_company=request.user.company),
        'transactions': AccountHistory.objects.filter()
    }
    return render(request, 'users/clients_applications.html', context=context)


def client_application(request):
    if request.method == 'POST':
        company = Company.objects.filter(id=request.user.company.id).first()
        company.application_form = request.FILES.get('application_form')
        company.save()
        return redirect('users:clients')


@login_required()
def download_application(request, id):
    user_permission(request)
    application = Account.objects.filter(id=id).first()
    if application:
        filename = application.application_document.name.split('/')[-1]
        response = HttpResponse(application.application_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect('users:clients')
    return response


@login_required()
def download_tax_clearance(request, id):
    user_permission(request)
    application = Account.objects.filter(id=id).first()
    if application:
        filename = application.tax_clearance.name.split('/')[-1]
        response = HttpResponse(application.tax_clearance, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect('users:clients')
    return response


@login_required()
def download_cr14(request, id):
    user_permission(request)
    application = Account.objects.filter(id=id).first()
    if application:
        filename = application.cr14.name.split('/')[-1]
        response = HttpResponse(application.cr14, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect('users:clients')
    return response


@login_required()
def download_cr6(request, id):
    user_permission(request)
    application = Account.objects.filter(id=id).first()
    if application:
        filename = application.cr6.name.split('/')[-1]
        response = HttpResponse(application.cr6, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect('users:clients')
    return response


@login_required()
def download_proof_of_residence(request, id):
    user_permission(request)
    application = Account.objects.filter(id=id).first()
    if application:
        filename = application.proof_of_residence.name.split('/')[-1]
        response = HttpResponse(application.proof_of_residence, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect('users:clients')
    return response


@login_required()
def download_cert_of_inc(request, id):
    user_permission(request)
    application = Account.objects.filter(id=id).first()
    if application:
        filename = application.cert_of_inc.name.split('/')[-1]
        response = HttpResponse(application.cert_of_inc, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect('users:clients')
    return response


@login_required()
def download_document(request, id):
    user_permission(request)
    document = Account.objects.filter(id=id).first()
    if document:
        filename = document.id_document.name.split('/')[-1]
        response = HttpResponse(document.id_document, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect('users:clients')
    return response


@login_required
def application_approval(request, id):
    user_permission(request)
    if request.method == "POST":
        new_account = request.POST['account_number']
        all_accounts = Account.objects.filter(supplier_company=request.user.company)
        accounts_list = []
        for account in all_accounts:
            accounts_list.append(account.account_number)
        if new_account in accounts_list:
            messages.warning(request, 'Account number already exists.')
            return redirect('users:clients')
        else:
            account = Account.objects.filter(id=id).first()
            account.is_verified = True
            account.account_number = new_account
            account.save()
            messages.success(request, 'Account successfully approved.')
            return redirect('users:clients')


@login_required
@user_role
def upload_users(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        if file is not None:
            if file.name.endswith('.csv') or file.name.endswith('.xlsx'):
                if file.name.endswith('.csv'):
                    df = pd.DataFrame(pd.read_csv(file))
                    try:
                        for index, row in df.iterrows():
                            # email or phone exists
                            if User.objects.filter(email=row['EMAIL']) or User.objects.filter(
                                    phone_number=row['PHONE NUMBER']):
                                pass
                            else:
                                password = secrets.token_hex(3)
                                username = row['SURNAME'] + row['NAME']
                                # create user
                                user = User.objects.create_user(username=username, password=password)

                                # look for company
                                if Company.objects.filter(name=row['COMPANY NAME']).exists():
                                    company = Company.objects.filter(name=row['COMPANY NAME']).first()

                                    # updating user company details
                                    user.company = company
                                    user.user_type = 'BUYER'
                                    user.email = row['EMAIL'].upper()
                                    user.password_reset = True
                                    user.phone_number = row['PHONE NUMBER']
                                    user.first_name = row['NAME']
                                    user.last_name = row['SURNAME']
                                    user.save()

                                    # creating account with supplier
                                    if Account.objects.filter(buyer_company=company).exists():
                                        # do nothing
                                        pass
                                    else:
                                        Account.objects.create(
                                            supplier_company=request.user.company,
                                            buyer_company=company,
                                            account_number=row['ACCOUNT NUMBER'.upper()],
                                            applied_by=user,
                                            is_verified=True,

                                        )

                                    # send email
                                    sender = f'ZFMS Accounts Accounts<{settings.EMAIL_HOST_USER}>'
                                    title = f'Account Creation By {request.user.company.name}'
                                    message = f"Dear {user.first_name}, {request.user.company.name} has created an account" \
                                              f"for you on Fuel Finder. Here are the details\n\n" \
                                              f"Username  :  {user.username}\n" \
                                              f"Password  :   {password}"
                                    # send email
                                    try:
                                        msg = EmailMultiAlternatives(title, message, sender, [user.email])
                                        msg.send()
                                    # if error occurs
                                    except BadHeaderError:
                                        pass
                                        # error log should be created

                                # company doesn't exists, create it
                                else:
                                    company = Company.objects.create(
                                        name=row['COMPANY NAME'],
                                        company_type='BUYER'
                                    )

                                    user.company = company
                                    user.user_type = 'BUYER'
                                    user.email = row['EMAIL'].upper()
                                    user.password_reset = True
                                    user.phone_number = row['PHONE NUMBER']
                                    user.first_name = row['NAME']
                                    user.last_name = row['SURNAME']
                                    user.save()

                                    # creating account with supplier
                                    if Account.objects.filter(buyer_company=company).exists():
                                        # do nothing
                                        pass
                                    else:
                                        Account.objects.create(
                                            supplier_company=request.user.company,
                                            buyer_company=company,
                                            account_number=row['ACCOUNT NUMBER'.upper()],
                                            applied_by=user,
                                            is_verified=True,

                                        )

                                    # send email
                                    sender = f'ZFMS Accounts Accounts<{settings.EMAIL_HOST_USER}>'
                                    title = f'Account Creation By Fuel Supplier {request.user.company.name}'
                                    message = f"Dear {user.first_name}, {request.user.company.name} has created an account" \
                                              f"for you on Fuel Finder. Here are the details\n\n" \
                                              f"Username  :  {user.username}\"" \
                                              f"Password  :   {password}"
                                    # send email
                                    try:
                                        msg = EmailMultiAlternatives(title, message, sender, [user.email])
                                        msg.send()
                                    # if error occurs
                                    except BadHeaderError:
                                        pass
                                        # error log should be created

                        messages.success(request, 'Successfully uploaded data.')
                        return redirect('users:clients')
                    except KeyError:
                        messages.warning(request, 'Please use the standard file.')
                        return redirect('users:clients')
                elif file.name.endswith('.xlsx'):
                    df = pd.DataFrame(pd.read_excel(file))
                    try:
                        for index, row in df.iterrows():
                            # email or phone exists
                            if User.objects.filter(email=row['EMAIL']) or User.objects.filter(
                                    phone_number=row['PHONE NUMBER']):
                                pass
                            else:
                                password = secrets.token_hex(3)
                                username = row['SURNAME'] + row['NAME']
                                # create user
                                user = User.objects.create_user(username=username, password=password)

                                # look for company
                                if Company.objects.filter(name=row['COMPANY NAME']).exists():
                                    company = Company.objects.filter(name=row['COMPANY NAME']).first()

                                    # updating user company details
                                    user.company = company
                                    user.user_type = 'BUYER'
                                    user.password_reset = True
                                    user.email = row['EMAIL'].upper()
                                    user.phone_number = row['PHONE NUMBER']
                                    user.first_name = row['NAME']
                                    user.last_name = row['SURNAME']
                                    user.save()

                                    # creating account with supplier
                                    if Account.objects.filter(buyer_company=company).exists():
                                        # do nothing
                                        pass
                                    else:
                                        Account.objects.create(
                                            supplier_company=request.user.company,
                                            buyer_company=company,
                                            account_number=row['ACCOUNT NUMBER'.upper()],
                                            applied_by=user,
                                            is_verified=True,
                                        )

                                    # send email
                                    sender = f'ZFMS Accounts Accounts<{settings.EMAIL_HOST_USER}>'
                                    title = f'Account Creation By Fuel Supplier {request.user.company.name}'
                                    message = f"Dear {user.first_name}, {request.user.company.name} has created an account" \
                                              f"for you on Fuel Finder. Here are the details\n\n" \
                                              f"Username  :  {user.username}\"" \
                                              f"Password  :   {password}"
                                    # send email
                                    try:
                                        msg = EmailMultiAlternatives(title, message, sender, [user.email])
                                        msg.send()
                                    # if error occurs
                                    except BadHeaderError:
                                        pass
                                        # error log should be created

                                # company doesn't exists, create it
                                else:
                                    company = Company.objects.create(
                                        name=row['COMPANY NAME'.upper()],
                                        company_type='BUYER'
                                    )

                                    user.company = company
                                    user.user_type = 'BUYER'
                                    user.password_reset = True
                                    user.email = row['EMAIL']
                                    user.phone_number = row['PHONE NUMBER']
                                    user.first_name = row['NAME']
                                    user.last_name = row['SURNAME']
                                    user.save()

                                    # creating account with supplier
                                    if Account.objects.filter(buyer_company=company).exists():
                                        # do nothing.
                                        pass
                                    else:
                                        Account.objects.create(
                                            supplier_company=request.user.company,
                                            buyer_company=company,
                                            account_number=row['ACCOUNT NUMBER'.upper()],
                                            applied_by=user,
                                            is_verified=True,

                                        )

                                    # send email
                                    sender = f'ZFMS Accounts Accounts<{settings.EMAIL_HOST_USER}>'
                                    title = f'Account Creation By {request.user.company.name}'
                                    message = f"Dear {user.first_name}, {request.user.company.name} has created an account" \
                                              f"for you on Fuel Finder. Here are the details\n\n" \
                                              f"Username  :  {user.username}\n" \
                                              f"Password  :   {password}"
                                    # send email
                                    try:
                                        msg = EmailMultiAlternatives(title, message, sender, [user.email])
                                        msg.send()
                                    # if error occurs
                                    except BadHeaderError:
                                        pass
                                        # error log should be created

                        messages.success(request, 'Successfully uploaded data.')
                        return redirect('users:clients')
                    except KeyError:
                        messages.warning(request, 'Please use the standard file.')
                        return redirect('users:clients')
            else:
                messages.warning(request, "Uploaded file doesn't meet the required format.")
                return redirect('users:clients')
        elif request.POST.get('account_id') is not None:
            buyer_transactions = AccountHistory.objects.filter(account_id=int(request.POST.get('account_id')))
            html_string = render_to_string('supplier/export.html', {'transactions': buyer_transactions})
            html = HTML(string=html_string, base_url=request.build_absolute_uri())

            export_name = f"{request.POST.get('buyer_name')}{date.today().strftime('%H%M%S')}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = 'attachment;filename=export.pdf'
                return response


@login_required()
@user_role
def place_order(request):
    fuel_object = DepotFuelUpdate.objects.first()
    diesel_rtgs_price = 0
    diesel_usd_price = 0
    petrol_rtgs_price = 0
    petrol_usd_price = 0
    if fuel_object is not None:
        diesel_rtgs_price = fuel_object.rtgs_diesel_price
        diesel_usd_price = fuel_object.usd_diesel_price
        petrol_rtgs_price = fuel_object.rtgs_petrol_price
        petrol_usd_price = fuel_object.usd_petrol_price
    else:
        pass
    if request.method == 'POST':
        company = request.user.company
        quantity = request.POST['quantity']
        currency = request.POST['currency']
        fuel_type = request.POST['fuel_type']
        if fuel_type.lower() == 'petrol':
            if currency == 'USD':
                price = petrol_usd_price
            else:
                price = petrol_rtgs_price
            proof_of_payment = request.FILES.get('proof_of_payment')
            depot_id = request.POST.get('depot')
            noic_depot = NoicDepot.objects.filter(id=depot_id).first()
            amount_paid = request.POST['fuel_paid']
            transporter = request.POST['transporter']
            truck_reg = request.POST['truck_reg']
            trailer_reg = request.POST['trailer_reg']
            driver = request.POST['driver']
            driver_id = request.POST['driver_id']
            status='Pending'
            order = Order.objects.create(status=status, price=price, noic_depot=noic_depot, amount_paid=amount_paid,
                                         transporter=transporter, truck_reg=truck_reg, trailer_reg=trailer_reg,
                                         driver=driver, driver_id=driver_id, company=company, quantity=quantity,
                                         currency=currency, fuel_type=fuel_type, proof_of_payment=proof_of_payment)
            order.save()

            message = f'{request.user.company.name.title()} placed an order of {quantity}L' \
                      f' {fuel_type.lower}'
            my_company = request.user.company
            Notification.objects.create(handler_id=1, message=message, company=my_company, reference_id=order.id,
                                        depot_id=noic_depot.id, action="ORDER")
            messages.success(request, 'Placed order successfully.')
            return redirect('users:orders')
        else:
            if currency == 'USD':
                price = diesel_usd_price
            else:
                price = diesel_rtgs_price
            proof_of_payment = request.FILES.get('proof_of_payment')
            depot_id = request.POST.get('depot')
            noic_depot = NoicDepot.objects.filter(id=depot_id).first()
            amount_paid = request.POST['fuel_paid']
            transporter = request.POST['transporter']
            truck_reg = request.POST['truck_reg']
            trailer_reg = request.POST['trailer_reg']
            driver = request.POST['driver']
            driver_id = request.POST['driver_id']
            status='Pending'
            order = Order.objects.create(status=status, price=price, noic_depot=noic_depot, amount_paid=amount_paid, transporter=transporter,
                                 truck_reg=truck_reg, trailer_reg=trailer_reg, driver=driver, driver_id=driver_id,
                                 company=company, quantity=quantity, currency=currency, fuel_type=fuel_type,
                                 proof_of_payment=proof_of_payment)

            order.save()

            message = f'{request.user.company.name.title()} placed an order of {quantity}L' \
                      f' {fuel_type.lower}'
            my_company = request.user.company
            Notification.objects.create(handler_id=1, message=message, reference_id=order.id, company=my_company,
                                        depot_id=noic_depot.id, action="ORDER")
            messages.success(request, 'Placed order successfully.')
            return redirect('users:orders')


@login_required()
@user_role
def orders(request):
    fuel_object = DepotFuelUpdate.objects.first()
    diesel_rtgs_price = 0
    diesel_usd_price = 0
    petrol_rtgs_price = 0
    petrol_usd_price = 0
    if fuel_object is not None:
        diesel_rtgs_price = fuel_object.rtgs_diesel_price
        diesel_usd_price = fuel_object.usd_diesel_price
        petrol_rtgs_price = fuel_object.rtgs_petrol_price
        petrol_usd_price = fuel_object.usd_petrol_price
    
    form1 = DepotContactForm()
    depots = NoicDepot.objects.filter(is_active=True).all()
    form1.fields['depot'].choices = [((depot.id, depot.name)) for depot in depots]
    accepted_orders = Order.objects.filter(company=request.user.company).filter(~Q(status='Pending')).all()
    pending_orders = Order.objects.filter(company=request.user.company).filter(status='Pending').all()
    for order in accepted_orders:
        sord = SordNationalAuditTrail.objects.filter(order=order).first()
        if sord is not None:
            order.allocation = sord
        else:
            order.allocation = None

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
            accepted_orders = Order.objects.filter(company=request.user.company).filter(~Q(status='Pending')).filter(date__range=[start_date, end_date])
            pending_orders = Order.objects.filter(company=request.user.company).filter(status='Pending').filter(date__range=[start_date, end_date])  
            
            for order in accepted_orders:
                sord = SordNationalAuditTrail.objects.filter(order=order).first()
                if sord is not None:
                    order.allocation = sord
                else:
                    order.allocation = None
            
            return render(request, 'users/orders.html',
                  {'depots': depots, 'form1': form1, 'diesel_rtgs_price': diesel_rtgs_price,
                   'diesel_usd_price': diesel_usd_price, 'petrol_rtgs_price': petrol_rtgs_price,
                   'petrol_usd_price': petrol_usd_price, 'accepted_orders': accepted_orders, 'pending_orders': pending_orders,
                   'start_date':start_date, 'end_date':end_date})
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
                accepted_orders = Order.objects.filter(company=request.user.company).filter(~Q(status='Pending')).filter(date__range=[start_date, end_date])
                pending_orders = Order.objects.filter(company=request.user.company).filter(status='Pending').filter(date__range=[start_date, end_date])
            
            accepted_orders = accepted_orders.values('date','noic_depot__name', 'fuel_type', 'quantity', 'currency', 'status')
            pending_orders =  pending_orders.values('date','noic_depot__name', 'fuel_type', 'quantity', 'currency', 'status')
            fields = ['date','noic_depot__name', 'fuel_type', 'quantity', 'currency', 'status']
            
            df_accepted_orders = pd.DataFrame(accepted_orders, columns=fields)
            df_pending_orders = pd.DataFrame(pending_orders, columns=fields)
            
            df = df_accepted_orders.append(df_pending_orders)

            
            filename = f'{request.user.company.name} - {date}.csv'
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
                accepted_orders = Order.objects.filter(company=request.user.company).filter(~Q(status='Pending')).filter(date__range=[start_date, end_date])
                pending_orders = Order.objects.filter(company=request.user.company).filter(status='Pending').filter(date__range=[start_date, end_date])   
            html_string = render_to_string('users/export/export_orders.html', {'accepted_orders': accepted_orders,'pending_orders':pending_orders,'date':today, 'start_date':start_date, 'end_date':end_date})
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} -Orders - {today}.pdf'
                return response        

    return render(request, 'users/orders.html',
                  {'depots': depots, 'form1': form1, 'diesel_rtgs_price': diesel_rtgs_price,
                   'diesel_usd_price': diesel_usd_price, 'petrol_rtgs_price': petrol_rtgs_price,
                   'petrol_usd_price': petrol_usd_price, 'accepted_orders': accepted_orders, 'pending_orders': pending_orders})


@login_required()
def view_release_note(request, id):
    user_permission(request)
    allocation = SordNationalAuditTrail.objects.filter(id=id).first()
    allocation.admin = request.user
    allocation.rep = User.objects.filter(subsidiary_id=allocation.assigned_depot.id).first()
    context = {
        'allocation': allocation
    }
    return render(request, 'users/release_note.html', context=context)


@login_required()
def delivery_note(request, id):
    user_permission(request)
    allocation = SordNationalAuditTrail.objects.filter(id=id).first()
    if request.method == 'POST':
        if allocation is not None:
            allocation.d_note = request.FILES.get('d_note')
            allocation.order.status = 'Complete'
            allocation.save()
            messages.success(request, 'Delivery note successfully uploaded.')

            message = f'{request.user.company.name.title()} uploaded delivery note'
            my_company = request.user.company
            noic_depot = allocation.order.noic_depot
            Notification.objects.create(handler_id=2, message=message, company=my_company, reference_id=allocation.order.id,
                                        depot_id=noic_depot.id, action="D-NOTE")
            return redirect('users:orders')
        else:
            pass


@login_required()
def download_proof(request, id):
    user_permission(request)
    document = Order.objects.filter(id=id).first()
    if document:
        filename = document.proof_of_payment.name.split('/')[-1]
        response = HttpResponse(document.proof_of_payment, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        messages.warning(request, 'Document not found.')
        return redirect('users:orders')
    return response


@login_required()
def delivery_schedules(request):
    user_permission(request)
    schedules = DeliverySchedule.objects.filter(transaction__supplier__company=request.user.company).all()

    for schedule in schedules:
        schedule.depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
        if schedule.transaction.offer.delivery_method.lower() == 'delivery':
            schedule.delivery_address = schedule.transaction.offer.request.delivery_address
        else:
            schedule.delivery_address = schedule.transaction.offer.collection_address
        
    completed_schedules = schedules.filter(confirmation_date__isnull=False)
    pending_schedules = schedules.filter(confirmation_date__isnull=True)

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
            schedules = DeliverySchedule.objects.filter(transaction__supplier__company=request.user.company).filter(date__range=[start_date, end_date])
            completed_schedules = []
            pending_schedules =[]
            for schedule in schedules:
                schedule.depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                if schedule.transaction.offer.delivery_method.lower() == 'delivery':
                    schedule.delivery_address = schedule.transaction.offer.request.delivery_address
                else:
                    schedule.delivery_address = schedule.transaction.offer.collection_address
                if schedule.confirmation_date:
                    completed_schedules.append(schedule)
                else:
                    pending_schedules.append(schedule)

            return render(request, 'users/delivery_schedules.html', {'pending_schedules': pending_schedules, 'completed_schedules': completed_schedules,
            'start_date':start_date, 'end_date':end_date })

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
                # schedules = DeliverySchedule.objects.filter(transaction__supplier__company=request.user.company).filter(date__range=[start_date, end_date])
                # completed_schedules = []
                # pending_schedules =[]
                # for schedule in schedules:
                #     schedule.depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                #     if schedule.transaction.offer.delivery_method.lower() == 'delivery':
                #         schedule.delivery_address = schedule.transaction.offer.request.delivery_address
                #     else:
                #         schedule.delivery_address = schedule.transaction.offer.collection_address
                #     if schedule.confirmation_date:
                #         completed_schedules.append(schedule)
                #     else:
                #         pending_schedules.append(schedule)
                completed_schedules = DeliverySchedule.objects.filter(transaction__supplier__company=request.user
                .company).filter(date__range=[start_date, end_date]).filter(confirmation_date__isnull=False)
                pending_schedules = DeliverySchedule.objects.filter(transaction__supplier__company=request.user
                .company).filter(date__range=[start_date, end_date]).filter(confirmation_date__isnull=True)


            # fields = ['date','transaction','driver_name', 'phone_number','id_number','vehicle_reg', 'delivery_time',
            # 'confirmation_date',  'transport_company','delivery_quantity','amount_for_fuel']

            df_completed_schedules = convert_to_dataframe(completed_schedules)
            df_pending_schedules = convert_to_dataframe(pending_schedules)

            # df_completed_schedules = pd.DataFrame(completed_schedules, fields)
            # df_pending_schedules = pd.DataFrame(pending_schedules, fields)

            df = df_completed_schedules.append(df_pending_schedules)
            df = df[['date','transaction','driver_name', 'phone_number','id_number','vehicle_reg', 'delivery_time',
            'confirmation_date',  'transport_company','delivery_quantity','amount_for_fuel']]
            filename = f'{request.user.company.name} - Delivery Schedules - {today}.csv'
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
                completed_schedules = []
                pending_schedules =[]
                for schedule in schedules:
                    schedule.depot = Subsidiaries.objects.filter(id=schedule.transaction.supplier.subsidiary_id).first()
                    if schedule.transaction.offer.delivery_method.lower() == 'delivery':
                        schedule.delivery_address = schedule.transaction.offer.request.delivery_address
                    else:
                        schedule.delivery_address = schedule.transaction.offer.collection_address
                    if schedule.confirmation_date:
                        completed_schedules.append(schedule)
                    else:
                        pending_schedules.append(schedule)  
            html_string = render_to_string('users/export/export_delivery_schedules.html', {'completed_schedules': completed_schedules,'pending_schedules':pending_schedules,'date':today, 'start_date':start_date, 'end_date':end_date})
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name.title()}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} -Orders - {today}.pdf'
                return response        
        

    return render(request, 'users/delivery_schedules.html', {'pending_schedules': pending_schedules, 'completed_schedules': completed_schedules})


'''
Change Password operation
'''


def notication_handler(request, id):
    my_handler = id
    if my_handler == 7:
        notifications = Notification.objects.filter(handler_id=my_handler).all()
        for notification in notifications:
            notification.is_read = True
            notification.save()
        return redirect('users:allocate')
    else:
        return redirect('users:allocate')


def notication_reader(request):
    notifications = Notification.objects.filter(action="FOR_FUEL").filter(is_read=False).all()
    for notification in notifications:
        notification.is_read = True
        notification.save()
    return redirect('users:allocate')