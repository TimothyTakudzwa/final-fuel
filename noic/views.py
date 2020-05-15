from datetime import datetime, timedelta, date
# from datetime import date

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from decimal import *

from company.models import Company
from fuelUpdates.models import SordCompanyAuditTrail
from fuelfinder.helper_functions import random_password
from national.models import DepotFuelUpdate, NoicDepot
from weasyprint import HTML

from noicDepot.models import Collections
from notification.models import Notification
from supplier.models import FuelAllocation
from users.forms import DepotContactForm
from users.models import Activity
from zeraPortal.lib import *
from zeraPortal.models import FuelPrices
from .lib import *
from .decorators import user_role, user_permission

today = date.today()

user = get_user_model()


@login_required()
@user_role
def orders(request):
    new_orders = Order.objects.filter(allocated_fuel=True).order_by('-date', '-time')
    orders = Order.objects.filter(allocated_fuel=False).order_by('-date', '-time')
    for order in orders:
        order.allocation = SordNationalAuditTrail.objects.filter(order=order).first()
    for order in new_orders:
        order.allocation = SordNationalAuditTrail.objects.filter(order=order).first()
    form1 = DepotContactForm()
    depots = NoicDepot.objects.all()
    form1.fields['depot'].choices = [((depot.id, depot.name)) for depot in depots]
    for order in orders:
        order.allocation = SordNationalAuditTrail.objects.filter(order=order).first()

    requests_notifications = Notification.objects.filter(action="MORE_FUEL").filter(is_read=False).all()
    for req in requests_notifications:
        if req is not None:
            req.is_read = True
            req.save()
        else:
            pass

    if request.method == "POST":
        if request.POST.get('start_date') and request.POST.get('end_date') :
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()

            new_orders = Order.objects.filter(allocated_fuel=True) \
            .filter(date__range=[start_date, end_date]).order_by('-date', '-time')
            orders = Order.objects.filter(allocated_fuel=False) \
            .filter(date__range=[start_date, end_date]).order_by('-date', '-time')

            for order in orders:
                order.allocation = SordNationalAuditTrail.objects.filter(order=order).first()
            for order in new_orders:
                order.allocation = SordNationalAuditTrail.objects.filter(order=order).first()

            form1 = DepotContactForm()

            depots = NoicDepot.objects.all()

            form1.fields['depot'].choices = [((depot.id, depot.name)) for depot in depots]

            for order in orders:
                order.allocation = SordNationalAuditTrail.objects.filter(order=order).first()

            requests_notifications = Notification.objects.filter(action="MORE_FUEL").filter(is_read=False).all()
            for req in requests_notifications:
                if req is not None:
                    req.is_read = True
                    req.save()
                else:
                    pass

            context = {
                'orders': orders,
                'form1': form1,
                'new_orders': new_orders,
                'start_date': start_date,
                'end_date': end_date
            }        


            return render(request, 'noic/orders.html', context=context)
            
                   
        if request.POST.get('export_to_csv')=='csv':
            start_date = request.POST.get('csv_start_date')
            end_date = request.POST.get('csv_end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                new_orders = Order.objects.filter(allocated_fuel=True) \
                .filter(date__range=[start_date, end_date]).order_by('-date', '-time')
                orders = Order.objects.filter(allocated_fuel=False) \
                .filter(date__range=[start_date, end_date]).order_by('-date', '-time')
               
            new_orders = new_orders.values('date','noic_depot__name', 'fuel_type', 'quantity', 'currency', 'status')
            orders =  orders.values('date','noic_depot__name', 'fuel_type', 'quantity', 'currency', 'status')
            fields = ['date','noic_depot__name', 'fuel_type', 'quantity', 'currency', 'status']
            
            df_orders = pd.DataFrame(new_orders, columns=fields)
            df_new_orders = pd.DataFrame(orders, columns=fields)

            df = df_orders.append(df_new_orders)

            # df = df[['date','noic_depot', 'fuel_type', 'quantity', 'currency', 'status']]
            filename = 'NOIC ADMIN'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - {today}.csv'
                return response     

        else:
            start_date = request.POST.get('pdf_start_date')
            end_date = request.POST.get('pdf_end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                new_orders = Order.objects.filter(allocated_fuel=True) \
                .filter(date__range=[start_date, end_date]).order_by('-date', '-time')
                orders = Order.objects.filter(allocated_fuel=False) \
                .filter(date__range=[start_date, end_date]).order_by('-date', '-time')
                   
            context = {
                'new_orders': new_orders,
                'orders':orders,
                'date':today,
                'start_date':start_date,
                 'end_date':end_date
            }

            html_string = render_to_string('noic/export/export_orders.html', context=context)
            html = HTML(string=html_string)
            export_name = f"Noic Admin"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} -Orders - {today}.pdf'
                return response        

        

    return render(request, 'noic/orders.html', {'orders': orders, 'form1': form1, 'new_orders': new_orders})


@login_required()
@user_role
def activity(request):
    filtered_activities = None
    activities = Activity.objects.filter(user=request.user).all()
    
    for activity in activities:
        if activity.action == 'Updating Prices':
            activity.fuel_update = DepotFuelUpdate.objects.filter(depot__id=activity.reference_id).first()
        
    current_activities = activities.filter(date=today)
    previous_activities = activities.exclude(date=today)     

    if request.method == "POST":
        if request.POST.get('start_date') and request.POST.get('end_date') :
            filtered = True;
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()
            
            filtered_activities = Activity.objects.filter(user=request.user).filter(date__range=[start_date, end_date])
            
            for activity in filtered_activities:
                if activity.action == 'Updating Prices':
                    activity.fuel_update = DepotFuelUpdate.objects.filter(depot__id=activity.reference_id).first()
       
            context = {
                'filtered_activities': filtered_activities,
                'start_date': start_date,
                'end_date': end_date,
            }

            return render(request, 'noic/activity.html', context=context)

        if request.POST.get('export_to_csv')=='csv':
            start_date = request.POST.get('csv_start_date')
            end_date = request.POST.get('csv_end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                filtered_activities = Activity.objects.filter(user=request.user).filter(date__range=[start_date, end_date])
                      
            fields = ['date','time', 'company__name', 'action', 'description', 'reference_id']
            
            if filtered_activities:
                filtered_activities = filtered_activities.values('date','time', 'company__name', 'action', 'description', 'reference_id')
                df = pd.DataFrame(filtered_activities, columns=fields)
            else:
                df_current = pd.DataFrame(current_activities.values('date','time', 'company__name', 'action', 'description', 'reference_id'), columns=fields)
                df_previous = pd.DataFrame(previous_activities.values('date','time', 'company__name', 'action', 'description', 'reference_id'), columns=fields)
                df = df_current.append(df_previous)

            filename = f'Noic Admin'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - Activities - {today}.csv'
                return response     

        else:
            start_date = request.POST.get('pdf_start_date')
            end_date = request.POST.get('pdf_end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                filtered_activities = Activity.objects.filter(user=request.user).filter(date__range=[start_date, end_date])

            context = {
                'filtered_activities': filtered_activities,
                'start_date':start_date,
                'current_activities': current_activities,
                'activities':previous_activities, 'end_date':end_date,
                'date':today
            }

            html_string = render_to_string('noic/export/export_activities.html', context=context)
            html = HTML(string=html_string)
            export_name = f"Noic Admin -"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} - Activities - {today}.pdf'
                return response




    return render(request, 'noic/activity.html', {'current_activities': current_activities, 'previous_activities': previous_activities})


@login_required()
@user_role
def dashboard(request):
    requests_notifications = Notification.objects.filter(action="MORE_FUEL").filter(is_read=False).all()
    num_of_requests = Notification.objects.filter(action="MORE_FUEL").filter(is_read=False).count()
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

    return render(request, 'noic/dashboard.html',
                  {'capacities': capacities, 'depots': depots, 'requests_notifications': requests_notifications,
                   'num_of_requests': num_of_requests, 'diesel_rtgs_price': diesel_rtgs_price,
                   'diesel_usd_price': diesel_usd_price, 'petrol_rtgs_price': petrol_rtgs_price,
                   'petrol_usd_price': petrol_usd_price, 'noic_usd_diesel': noic_usd_diesel,
                   'noic_rtgs_diesel': noic_rtgs_diesel, 'noic_usd_petrol': noic_usd_petrol,
                   'noic_rtgs_petrol': noic_rtgs_petrol})


@login_required()
@user_role
def edit_fuel(request):
    usd_fuel = NationalFuelUpdate.objects.filter(currency='USD').first()
    rtgs_fuel = NationalFuelUpdate.objects.filter(currency='RTGS').first()
    if request.method == 'POST':
        quantity = float(request.POST['quantity'])
        if request.POST['fuel_type'].lower() == 'petrol':
            if request.POST['currency'] == 'USD':
                usd_fuel.unallocated_petrol = quantity
                usd_fuel.save()
                messages.success(request, 'USD Petrol updated successfully')
            else:
                rtgs_fuel.unallocated_petrol = quantity
                rtgs_fuel.save()
                messages.success(request, 'RTGS petrol updated successfully')
        else:
            if request.POST['currency'] == 'USD':
                usd_fuel.unallocated_diesel = quantity
                usd_fuel.save()
                messages.success(request, 'USD diesel updated successfully')
            else:
                rtgs_fuel.unallocated_diesel = quantity
                rtgs_fuel.save()
                messages.success(request, 'RTGS diesel updated successfully')
    return redirect('noic:dashboard')



@login_required()
@user_role
def allocations(request):
    allocations = SordNationalAuditTrail.objects.all()
    date_today = datetime.date.today().strftime("%d/%m/%y")

    if request.method == "POST":
        if request.POST.get('start_date') and request.POST.get('end_date'):
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()
            allocations = SordNationalAuditTrail.objects.filter(date__range=[start_date, end_date])

            return render(request, 'noic/allocations.html',
                          {'allocations': allocations, 'start_date': start_date, 'end_date': end_date})
        if request.POST.get('export_to_csv')=='csv':
            start_date = request.POST.get('csv_start_date')
            end_date = request.POST.get('csv_end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                allocations = SordNationalAuditTrail.objects.filter(date__range=[start_date, end_date])

            allocations = allocations.values('date','time','sord_no','company','fuel_type','currency','quantity','price')
            fields = ['date','time','sord_no','company','fuel_type','currency','quantity','price']

            df = pd.DataFrame(allocations, columns=fields)
            filename = 'Noic Admin'

            df = df[['date','time','sord_no','company','fuel_type','currency','quantity','price']]
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename}- Allocations -{date_today}.csv'
                return response                  
        else:
            start_date = request.POST.get('pdf_start_date')
            end_date = request.POST.get('pdf_end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                allocations = SordNationalAuditTrail.objects.filter(date__range=[start_date, end_date])
            html_string = render_to_string('noic/export/export_audit.html', {'allocations': allocations, 'date': date})
            html = HTML(string=html_string)
            export_name = "Noic Allocations Summary"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} - {date_today}.pdf'
                return response

    return render(request, 'noic/allocations.html', {'allocations': allocations})


@login_required()
@user_role
def depots(request):
    global depot
    depots = NoicDepot.objects.all()
    form1 = DepotContactForm()
    zimbabwean_towns = ['Select City ---', 'Beitbridge', 'Bindura', 'Bulawayo', 'Chinhoyi', 'Chirundu', 'Gweru',
                        'Harare', 'Hwange', 'Juliusdale', 'Kadoma', 'Kariba', 'Karoi', 'Kwekwe', 'Marondera',
                        'Masvingo',
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
            messages.warning(request, 'Invalid email.')
            return redirect('noic:depots')

        name = request.POST['name']
        city = request.POST['city']
        location = request.POST['location']
        destination_bank = request.POST['destination_bank']
        account_number = request.POST['account_number']
        praz_reg_num = request.POST['praz']
        vat = request.POST['vat']
        license_num = request.POST['licence']
        depot = NoicDepot.objects.create(is_active=True, license_num=license_num, praz_reg_num=praz_reg_num,
                                         vat=vat, account_number=account_number,
                                         destination_bank=destination_bank, city=city, address=location,
                                         name=name)
        depot.save()

        depot_id = depot.id

        fuel_update = DepotFuelUpdate.objects.create(depot=depot)
        fuel_update.save()

        action = "Depot Creation"
        description = f"You have created another NOIC Depot {depot.name}"
        Activity.objects.create(depot=depot, user=request.user,
                                action=action, description=description, reference_id=depot.id)
        messages.success(request, 'Depot created successfully.')

        depots = NoicDepot.objects.all()

        return render(request, 'noic/depots.html',
                      {'depots': depots, 'form1': form1, 'add_user': 'show', 'Harare': Harare, 'Bulawayo': Bulawayo,
                       'zimbabwean_towns': zimbabwean_towns,
                       'Mutare': Mutare, 'Gweru': Gweru, 'form': DepotContactForm(), 'depot': depot_id})

    return render(request, 'noic/depots.html',
                  {'depots': depots, 'add_user': 'hide', 'Harare': Harare, 'Bulawayo': Bulawayo,
                   'zimbabwean_towns': zimbabwean_towns,
                   'Mutare': Mutare, 'Gweru': Gweru, 'form1': form1, 'form': DepotContactForm()})


@login_required()
def edit_depot(request, id):
    user_permission(request)
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
            messages.success(request, 'Depot updated successfully.')
            return redirect('noic:depots')
        else:
            messages.success(request, 'Depot does not exists.')
            return redirect('noic:depots')


@login_required()
def delete_depot(request, id):
    user_permission(request)
    if request.method == 'POST':
        if NoicDepot.objects.filter(id=id).exists():
            depot_update = NoicDepot.objects.filter(id=id).first()
            activities = Activity.objects.filter(reference_id=depot_update.id)
            for activity in activities:
                activity.delete()
            depot_update.delete()

            # action = "Deleting Depot" 
            # description = f"You have deleted NOIC Depot {depot_update.name}"
            # Activity.objects.create(depot=depot_update, user=request.user,
            #                             action=action, description=description, reference_id=depot_update.id)
            messages.success(request, 'Depot deleted successfully.')
            return redirect('noic:depots')

        else:
            messages.success(request, 'Depot does not exists.')
            return redirect('noic:depots')


@login_required()
def fuel_update(request, id):
    user_permission(request)
    fuel_update = DepotFuelUpdate.objects.filter(id=id).first()
    prices = FuelPrices.objects.first()
    if request.method == 'POST':
        if request.POST['fuel_type'].lower() == 'petrol':
            if request.POST['currency'] == 'USD':
                if Decimal(request.POST['petrol_usd_price']) > prices.usd_petrol_pumpprice:
                    messages.warning(request,
                                     f'You cannot set USD petrol price higher that the ZERA max price of ${prices.usd_petrol_pumpprice}.')
                    return redirect('noic:dashboard')
                else:
                    fuel_update.usd_petrol += float(request.POST['quantity'])
                    fuel_update.usd_petrol_price = request.POST['petrol_usd_price']
                    fuel_update.save()

                    action = "Fuel Allocation"
                    description = f"You have allocated fuel to {fuel_update.depot.name}"
                    Activity.objects.create(fuel_type='Petrol', quantity=float(request.POST['quantity']),
                                            currency='USD', price=fuel_update.usd_petrol_price, depot=fuel_update.depot,
                                            user=request.user,
                                            action=action, description=description, reference_id=fuel_update.id)
                    messages.success(request, 'Updated petrol quantity successfully.')
                    return redirect('noic:dashboard')
            else:
                if Decimal(request.POST['petrol_rtgs_price']) > prices.rtgs_petrol_pumpprice:
                    messages.warning(request,
                                     f'You cannot set RTGS petrol price higher that the ZERA max price of ${prices.rtgs_petrol_pumpprice}.')
                    return redirect('noic:dashboard')
                else:
                    fuel_update.rtgs_petrol += float(request.POST['quantity'])
                    fuel_update.rtgs_petrol_price = request.POST['petrol_rtgs_price']
                    fuel_update.save()

                    action = "Fuel Allocation"
                    description = f"You have allocated fuel to {fuel_update.depot.name}"
                    Activity.objects.create(fuel_type='Petrol', quantity=float(request.POST['quantity']),
                                            currency='RTGS', price=fuel_update.rtgs_petrol_price,
                                            depot=fuel_update.depot, user=request.user,
                                            action=action, description=description, reference_id=fuel_update.id)
                    messages.success(request, 'Updated petrol quantity successfully.')
                    return redirect('noic:dashboard')

        else:
            if request.POST['currency'] == 'USD':
                if Decimal(request.POST['diesel_usd_price']) > prices.usd_diesel_pumpprice:
                    messages.warning(request,
                                     f'You cannot set USD diesel price higher that the ZERA max price of ${prices.usd_diesel_pumpprice}.')
                    return redirect('noic:dashboard')
                else:
                    fuel_update.usd_diesel += float(request.POST['quantity'])
                    fuel_update.usd_diesel_price = request.POST['diesel_usd_price']
                    fuel_update.save()

                    action = "Fuel Allocation"
                    description = f"You have allocated fuel to {fuel_update.depot.name}"
                    Activity.objects.create(fuel_type='Diesel', quantity=float(request.POST['quantity']),
                                            currency='USD', price=fuel_update.usd_diesel_price, depot=fuel_update.depot,
                                            user=request.user,
                                            action=action, description=description, reference_id=fuel_update.id)
                    messages.success(request, 'Updated diesel quantity successfully.')
                    return redirect('noic:dashboard')
            else:
                if Decimal(request.POST['diesel_rtgs_price']) > prices.rtgs_diesel_pumpprice:
                    messages.warning(request,
                                     f'You cannot set RTGS diesel price higher that the ZERA max price of ${prices.rtgs_diesel_pumpprice}.')
                    return redirect('noic:dashboard')
                else:
                    fuel_update.rtgs_diesel += float(request.POST['quantity'])
                    fuel_update.rtgs_diesel_price = request.POST['diesel_rtgs_price']
                    fuel_update.save()
                    action = "Fuel Allocation"
                    description = f"You have allocated fuel to {fuel_update.depot.name}"
                    Activity.objects.create(fuel_type='Diesel', quantity=float(request.POST['quantity']),
                                            currency='RTGS', price=fuel_update.rtgs_diesel_price,
                                            depot=fuel_update.depot, user=request.user,
                                            action=action, description=description, reference_id=fuel_update.id)
                    messages.success(request, 'Updated diesel quantity successfully.')
                    return redirect('noic:dashboard')


@login_required()
def edit_prices(request, id):
    user_permission(request)
    fuel_update = DepotFuelUpdate.objects.filter(id=id).first()
    prices = FuelPrices.objects.first()
    if request.method == 'POST':
        if Decimal(request.POST['usd_petrol_price']) > prices.usd_petrol_pumpprice:
            messages.warning(request,
                             f'You cannot set USD petrol price higher that the ZERA max price of ${prices.usd_petrol_pumpprice}.')
            return redirect('noic:dashboard')
        else:
            if Decimal(request.POST['usd_diesel_price']) > prices.usd_diesel_pumpprice:
                messages.warning(request,
                                 f'You cannot set USD diesel price higher that the ZERA max price of ${prices.usd_diesel_pumpprice}.')
                return redirect('noic:dashboard')

            else:
                if Decimal(request.POST['rtgs_petrol_price']) > prices.rtgs_petrol_pumpprice:
                    messages.warning(request,
                                     f'You cannot set RTGS petrol price higher that the ZERA max price of ${prices.rtgs_petrol_pumpprice}.')
                    return redirect('noic:dashboard')
                else:
                    if Decimal(request.POST['rtgs_diesel_price']) > prices.rtgs_diesel_pumpprice:
                        messages.warning(request,
                                         f'You cannot set RTGS diesel price higher that the ZERA max price of ${prices.rtgs_diesel_pumpprice}.')
                        return redirect('noic:dashboard')
                    else:
                        fuel_update.usd_petrol_price = request.POST['usd_petrol_price']
                        fuel_update.usd_diesel_price = request.POST['usd_diesel_price']
                        fuel_update.rtgs_petrol_price = request.POST['rtgs_petrol_price']
                        fuel_update.rtgs_diesel_price = request.POST['rtgs_diesel_price']
                        fuel_update.save()

                        action = "Updating Prices"
                        description = f"You have updated fuel prices for {fuel_update.depot.name}"
                        Activity.objects.create(depot=fuel_update.depot, user=request.user,
                                                action=action, description=description,
                                                reference_id=fuel_update.depot.id)
                        messages.success(request, 'Updated prices successfully.')
                        return redirect('noic:dashboard')


@login_required()
def payment_approval(request, id):
    user_permission(request)
    order = Order.objects.filter(id=id).first()
    order.payment_approved = True
    order.save()
    messages.success(request, 'Payment approved successfully.')
    return redirect('noic:orders')


@login_required()
def allocate_fuel(request, id):
    user_permission(request)
    order = Order.objects.filter(id=id).first()

    if request.method == 'POST':
        if request.POST['fuel_type'].lower() == 'petrol':
            if request.POST['currency'] == 'USD':
                noic_capacity = NationalFuelUpdate.objects.filter(currency='USD').first()
                if float(request.POST['quantity']) > noic_capacity.unallocated_petrol:
                    messages.warning(request,
                                     f'You cannot allocate fuel more than your capacity of {noic_capacity.unallocated_petrol}L.')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_petrol -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company,
                                                                        fuel_type=request.POST['fuel_type'],
                                                                        currency=request.POST['currency'],
                                                                        quantity=float(request.POST['quantity']),
                                                                        allocated_by=request.user,
                                                                        allocated_to=order.company)
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no,
                                                         action_no=0, action='Receiving Fuel',
                                                         fuel_type=sord_object.fuel_type,
                                                         payment_type=sord_object.currency,
                                                         initial_quantity=float(request.POST['quantity']),
                                                         end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.usd_petrol_price = noic_capacity.petrol_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()

                    messages.success(request, 'Fuel allocated successfully.')
                    return redirect('noic:orders')

            else:
                noic_capacity = NationalFuelUpdate.objects.filter(currency='RTGS').first()
                if float(request.POST['quantity']) > noic_capacity.unallocated_petrol:
                    messages.warning(request,
                                     f'You cannot allocate fuel more than your capacity of {noic_capacity.unallocated_petrol}L.')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_petrol -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company,
                                                                        fuel_type=request.POST['fuel_type'],
                                                                        currency=request.POST['currency'],
                                                                        quantity=float(request.POST['quantity']),
                                                                        allocated_by=request.user,
                                                                        allocated_to=order.company)
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no,
                                                         action_no=0, action='Receiving Fuel',
                                                         fuel_type=sord_object.fuel_type,
                                                         payment_type=sord_object.currency,
                                                         initial_quantity=float(request.POST['quantity']),
                                                         end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.petrol_price = noic_capacity.petrol_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'Fuel allocated successfully.')
                    return redirect('noic:orders')


        else:
            if request.POST['currency'] == 'USD':
                noic_capacity = NationalFuelUpdate.objects.filter(currency='USD').first()
                if float(request.POST['quantity']) > noic_capacity.unallocated_diesel:
                    messages.warning(request,
                                     f'You cannot allocate fuel more than your capacity of {noic_capacity.unallocated_diesel}L.')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company,
                                                                        fuel_type=request.POST['fuel_type'],
                                                                        currency=request.POST['currency'],
                                                                        quantity=float(request.POST['quantity']),
                                                                        allocated_by=request.user,
                                                                        allocated_to=order.company)
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no,
                                                         action_no=0, action='Receiving Fuel',
                                                         fuel_type=sord_object.fuel_type,
                                                         payment_type=sord_object.currency,
                                                         initial_quantity=float(request.POST['quantity']),
                                                         end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.usd_diesel_price = noic_capacity.diesel_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'Fuel allocated successfully.')
                    return redirect('noic:orders')


            else:
                noic_capacity = NationalFuelUpdate.objects.filter(currency='RTGS').first()
                if float(request.POST['quantity']) > noic_capacity.unallocated_diesel:
                    messages.warning(request,
                                     f'You cannot allocate fuel more than your capacity of {noic_capacity.unallocated_diesel}L.')
                    return redirect('noic:orders')
                else:
                    noic_capacity.unallocated_diesel -= float(request.POST['quantity'])
                    noic_capacity.save()
                    sord_object = SordNationalAuditTrail.objects.create(company=order.company,
                                                                        fuel_type=request.POST['fuel_type'],
                                                                        currency=request.POST['currency'],
                                                                        quantity=float(request.POST['quantity']),
                                                                        allocated_by=request.user,
                                                                        allocated_to=order.company)
                    sord_object.sord_no = sord_object.id
                    sord_object.save()
                    SordCompanyAuditTrail.objects.create(company=order.company, sord_no=sord_object.sord_no,
                                                         action_no=0, action='Receiving Fuel',
                                                         fuel_type=sord_object.fuel_type,
                                                         payment_type=sord_object.currency,
                                                         initial_quantity=float(request.POST['quantity']),
                                                         end_quantity=float(request.POST['quantity']))
                    company_update = CompanyFuelUpdate.objects.filter(company=order.company).first()
                    company_update.unallocated_petrol += float(request.POST['quantity'])
                    company_update.diesel_price = noic_capacity.diesel_price
                    company_update.save()
                    order.allocated_fuel = True
                    order.save()
                    messages.success(request, 'Fuel allocated successfully.')
                    return redirect('noic:orders')


@login_required()
@user_role
def statistics(request):
    monthly_rev = get_monthly_orders()
    weekly_rev = get_weekly_orders(True)
    last_week_rev = get_weekly_orders(False)

    fuel_orders = Order.objects.filter(payment_approved=True).annotate(
        number_of_orders=Count('noic_depot')).order_by('-number_of_orders')
    all_clients = [order.noic_depot for order in fuel_orders]

    new_clients = []
    for client in all_clients:
        total_transactions = all_clients.count(client)
        new_client_orders = Order.objects.filter(noic_depot=client, payment_approved=True).all()
        total_value = 0
        total_client_orders = []
        number_of_orders = 0
        for tran in new_client_orders:
            total_value += (tran.amount_paid)
            total_client_orders.append(tran)
            number_of_orders += 1
        client.total_revenue = total_value
        client.total_client_orders = total_client_orders
        client.number_of_orders = total_transactions
        if client not in new_clients:
            new_clients.append(client)

    clients = sorted(new_clients, key=lambda x: x.total_revenue, reverse=True)

    return render(request, 'noic/statistics.html',
                  {'monthly_rev': monthly_rev, 'weekly_rev': weekly_rev, 'last_week_rev': last_week_rev,
                   'clients': clients})


@login_required()
@user_role
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
            messages.warning(request, f"The email {sup.email} is already in the system, please use a different email.")
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
        new_user = User.objects.create(company_position='manager', subsidiary_id=subsidiary_id,
                                       username=username.lower(),
                                       first_name=first_name, last_name=last_name, user_type='NOIC_STAFF', email=email,
                                       phone_number=phone_number, password_reset=True)
        new_user.set_password(password)
        depot = NoicDepot.objects.filter(id=subsidiary_id).first()
        depot.is_active = True
        depot.save()

        action = "Creating Staff"
        description = f"You have created user {new_user.first_name} for {depot.name}"
        Activity.objects.create(depot=depot, user=request.user, action=action, description=description,
                                reference_id=request.user.id, created_user=new_user)
        if message_is_send(request, new_user, password):
            if new_user.is_active:
                new_user.stage = 'menu'
                new_user.save()

            else:
                messages.warning(request, f"Oops , something went wrong, please try again.")
        return redirect('noic:staff')

    return render(request, 'noic/staff.html', {'depots': depots, 'form1': form1, 'staffs': staffs})


@login_required()
def message_is_send(request, user, password):
    user_permission(request)
    sender = "intelliwhatsappbanking@gmail.com"
    subject = 'ZFMS Registration'
    message = f"Dear {user.first_name}  {user.last_name}. \nYour Username is: {user.username}\nYour Initial Password is: {password} \n\nPlease login on Fuel Management System Website and access your assigned Depot & don't forget to change your password on user profile. \n. "
    try:
        msg = EmailMultiAlternatives(subject, message, sender, [f'{user.email}'])
        msg.send()
        messages.success(request,
                         f"{user.first_name.title()}  {user.last_name.title()} has been registered successfully.")
        return True
    except Exception as e:
        messages.warning(request,
                         f"Oops , something went wrong sending email, please make sure you have internet access.")
        return False
    return render(request, 'buyer/send_email.html')


@login_required()
@user_role
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
            stock = DepotFuelUpdate.objects.all()

            requests = None
            allocations = None
            orders = None
            revs = None
            verified_companies = None
            unverified_companies = None
        if request.POST.get('report_type') == 'Orders':
            orders = Order.objects.filter(date__range=[start_date, end_date])
            print('I am in orders')
            requests = None
            allocations = None
            revs = None
            verified_companies = None
            unverified_companies = None
        if request.POST.get('report_type') == 'Requests':
            requests = FuelRequest.objects.filter(date__range=[start_date, end_date])
            print(f'__________________{requests}__________________________________')
            orders = None
            allocations = None
            stock = None
            revs = None
            verified_companies = None
            unverified_companies = None
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
            unverified_companies = None
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
            verified_companies = None
        if request.POST.get('report_type') == 'Allocations':
            print("__________________________I am in allocations____________________________")
            allocations = NationalFuelUpdate.objects.all()
            print(f'________________________________{allocations}__________________________')
            requests = None
            revs = None
            stock = None
            verified_companies = None
            unverified_companies = None
        start = start_date
        end = end_date
    return render(request, 'noic/reports.html')


@login_required()
@user_role
def profile(request):
    user = request.user
    return render(request, 'noic/profile.html', {'user': user})


@login_required()
@user_role
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
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            start_date = start_date.date()
        report_type = request.POST.get('report_type')
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date.date()
        if request.POST.get('report_type') == 'Stock':
            stock = type('test', (object,), {})()
            # stock.date = datetime.today()
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
            allocations_per_supplier = []
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
                       'start': start, 'end': end, 'stock': stock,
                       'allocations_per_supplier': allocations_per_supplier})

    show = False
    return render(request, 'noic/reports.html',
                  {'orders': orders, 'pending_orders': pending_orders, 'complete_orders': complete_orders,
                   'start': start, 'end': end, 'stock': stock})


@login_required()
def depot_history(request, did):
    user_permission(request)
    depot = NoicDepot.objects.filter(id=did).first()
    trans = []
    state = 'All'

    if request.method == "POST":

        if request.POST.get('report_type') == 'Complete':
            trns = Order.objects.filter(noic_depot=depot, payment_approved=True)
            trans = []
            for tran in trns:
                tran.revenue = tran.quantity
                trans.append(tran)
            state = 'Complete'

        if request.POST.get('report_type') == 'Incomplete':
            trns = Order.objects.filter(noic_depot=depot, payment_approved=False)
            trans = []
            for tran in trns:
                tran.revenue = tran.quantity
                trans.append(tran)
            state = 'Incomplete'

        if request.POST.get('report_type') == 'All':
            trns = Order.objects.filter(noic_depot=depot)
            trans = []
            for tran in trns:
                tran.revenue = tran.quantity
                trans.append(tran)
            state = 'All'
        return render(request, 'noic/depot_history.html', {'trans': trans, 'depot': depot, 'state': state})

    trns = Order.objects.filter(noic_depot=depot)
    trans = []
    for tran in trns:
        tran.revenue = tran.quantity
        trans.append(tran)

    return render(request, 'noic/depot_history.html', {'trans': trans, 'depot': depot, 'state': state})


@login_required()
@user_role
def collections(request):
    filtered_collections = None
    collections = Collections.objects.exclude(date=today).order_by('-date', '-time')
    new_collections = Collections.objects.filter(date=today).order_by('-time')

    context = {
        'collections': collections ,
        'new_collections': new_collections
    }

    if request.method == 'POST':
        if request.POST.get('start_date') and request.POST.get('end_date') :
            filtered = True;
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()
            
            filtered_collections = Collections.objects.filter(date__range=[start_date, end_date]) \
            .order_by('-date','-time')

            context = {
                'start_date': start_date,
                'end_date': end_date,
                # 'form': CollectionsForm(),
                'filtered_collections': filtered_collections
            }

            return render(request, 'noic/collections.html', context=context)



        if request.POST.get('export_to_csv')=='csv':
            start_date = request.POST.get('csv_start_date')
            end_date = request.POST.get('csv_end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                filtered_collections = Collections.objects.filter(date__range=[start_date, end_date]) \
                .order_by('-date','-time')

                      
            fields = ['date','time', 'order__noic_depot__name', 'order__company__name', 'order__fuel_type', 'order__quantity']
            
            if filtered_collections:
                filtered_collections = filtered_collections.values('date','time', 'order__noic_depot__name', 'order__company__name', 'order__fuel_type', 'order__quantity')
                df = pd.DataFrame(filtered_collections, columns=fields)
            else:
                df_current = pd.DataFrame(new_collections.values('date','time', 'order__noic_depot__name', 'order__company__name', 'order__fuel_type', 'order__quantity'), columns=fields)
                df_previous = pd.DataFrame(collections.values('date','time', 'order__noic_depot__name', 'order__company__name', 'order__fuel_type', 'order__quantity'), columns=fields)
                df = df_current.append(df_previous)

            filename = f'Noic Admin Collections'
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - {today}.csv'
                return response     

        else:
            start_date = request.POST.get('pdf_start_date')
            end_date = request.POST.get('pdf_end_date')
            if start_date:
                start_date = datetime.datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                filtered_collections = Collections.objects.filter(date__range=[start_date, end_date]) \
                .order_by('-date','-time')

            context = {
                'start_date': start_date,
                'end_date': end_date,
                'date': today,
                'collections': collections,
                'new_collections': new_collections,
                'filtered_collections': filtered_collections
            }    

            html_string = render_to_string('noic/export/export_collections.html', context=context)
            html = HTML(string=html_string)
            export_name = "Noic Admin"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} - Collections - {today}.pdf'
                return response


    return render(request, 'noic/collections.html', context=context)


def notication_handler(request, id):
    my_handler = id
    if my_handler == 3:
        notifications = Notification.objects.filter(handler_id=my_handler).all()
        for notification in notifications:
            notification.is_read = True
            notification.save()
        return redirect('noic:dashboard')
    else:
        return redirect('noic:dashboard')


def notication_reader(request):
    notifications = Notification.objects.filter(action="MORE_FUEL").filter(is_read=False).all()
    for notification in notifications:
        notification.is_read = True
        notification.save()
    return redirect('noic:dashboard')


@login_required()
@user_role
def edit_user_details(request):
    if request.method == 'POST':
        current_user = User.objects.filter(id=int(request.POST.get('edit_user_id'))).first()
        # check if email was edited
        if current_user.email != request.POST.get('email'):
            if User.objects.filter(email=request.POST.get('email')).exists():
                messages.warning(request, 'Email exists already, use another email')
                return redirect('noic:staff')
        current_user.email = request.POST.get('email')
        current_user.first_name = request.POST.get('first_name')
        current_user.last_name = request.POST.get('last_name')
        # verify phone number
        current_user.phone_number = request.POST.get('phone_number')
        current_user.save()
        messages.success(request, 'Profile successfully saved')
        return redirect('noic:staff')


@login_required()
@user_role
def delete_user(request):
    if request.method == 'POST':
        User.objects.filter(id=int(request.POST.get('delete_user_id'))).delete()
        messages.success(request, 'User successfully deleted')
        return redirect('noic:staff')
