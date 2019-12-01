import random

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import Http404
from supplier.models import *
from supplier.forms import *
from buyer.models import *
from buyer.forms import *
from .forms import *
from .models import AuditTrail
import secrets
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from datetime import datetime
from django.contrib import messages
from buyer.models import *
from supplier.forms import *
from supplier.models import *
from users.models import *
from company.models import Company
from django.contrib.auth import authenticate
from .forms import AllocationForm
from company.models import FuelUpdate as F_Update
from django.contrib.auth import get_user_model
user = get_user_model()


def index(request):
    return render(request, 'users/index.html')


def allocate(request):
    allocates = F_Update.objects.filter(company_id=request.user.company.id).all()
    for allocate in allocates:
        subsidiary = Subsidiaries.objects.filter(id=allocate.relationship_id).first()
        allocate.subsidiary_name = subsidiary.name
    
    if request.method == 'POST':
        if F_Update.objects.filter(id= int(request.POST['id'])).exists():
            fuel_update = F_Update.objects.filter(id= int(request.POST['id'])).first()
            fuel_update.petrol_quantity = fuel_update.petrol_quantity + int(request.POST['petrol_quantity'])
            fuel_update.petrol_price = request.POST['petrol_price']
            fuel_update.diesel_quantity = fuel_update.diesel_quantity + int(request.POST['diesel_quantity'])
            fuel_update.diesel_price = request.POST['diesel_price']
            fuel_update.payment_methods = request.POST['payment_methods']
            fuel_update.queue_length = request.POST['queue_length']
            fuel_update.save()
            messages.success(request, 'updated quantities successfully')
            return redirect('users:allocate')
        else:
            messages.success(request, 'Subsidiary does not exists')
            return redirect('users:allocate')
    
    return render(request, 'users/allocate.html', {'allocates': allocates})

def statistics(request):
    company = request.user.company
    staff_blocked = Subsidiaries.objects.filter(company=company).count() / 2
    offers = Offer.objects.filter(supplier=request.user).count()
    bulk_requests = FuelRequest.objects.filter(delivery_method="BULK").count()
    normal_requests = FuelRequest.objects.filter(delivery_method="REGULAR").count()
    staff_blocked = User.objects.filter(company=company).count()
    clients = []
    #update = F_Update.objects.filter(company_id=company.id).first()
    diesel, petrol = 0
    # if update:
    #     diesel = update.diesel_quantity
    #     petrol = update.petrol_quantity
    
    companies = Company.objects.filter(company_type='BUYER')
    value = [round(random.uniform(5000.5,10000.5),2) for i in range(len(companies))]
    num_trans = [random.randint(2,12) for i in range(len(companies))]
    counter = 0

    for company in companies:
        company.total_value = value[counter]
        company.num_transactions = num_trans[counter]
        counter += 1

    clients = [company for company in  companies]    

    try:
        trans = Transaction.objects.all().count()/Transaction.objects.all().count()/100
    except:
        trans = 0    
    trans = str(trans) + " %"
    return render(request, 'users/statistics.html', {'staff_blocked':staff_blocked, 'offers': offers,
     'bulk_requests': bulk_requests, 'trans': trans, 'clients': clients, 'normal_requests': normal_requests,
     'diesel':diesel, 'petrol':petrol})


def supplier_user_edit(request, cid):
    supplier = User.objects.filter(id=cid).first()

    if request.method == "POST":
        #supplier.company = request.POST['company']
        supplier.phone_number = request.POST['phone_number']
        supplier.supplier_role = request.POST['user_type']
        #supplier.supplier_role = request.POST['supplier_role']
        supplier.save()
        messages.success(request, 'Your Changes Have Been Saved')
    return render(request, 'users/suppliers_list.html')

def myaccount(request):
    staff = user.objects.get(id=request.user.id)
    print(staff.username)
    if request.method == 'POST':
        staff.email = request.POST['email']
        staff.phone_number = request.POST['phone_number']
        staff.company_position = request.POST['company_position']
        staff.save()
        messages.success(request, 'Your Changes Have Been Saved')
       
    return render(request, 'users/profile.html')

def stations(request):
    stations = Subsidiaries.objects.all()
    if request.method == 'POST':
        name = request.POST['name']
        address = request.POST['address']
        is_depot = request.POST['is_depot']
        opening_time = request.POST['opening_time']
        closing_time = request.POST['closing_time']
        sub = Subsidiaries.objects.create(company=request.user.company,name=name,address=address,is_depot=is_depot,opening_time=opening_time,closing_time=closing_time)
    
        sub_type = 'service_station' if is_depot else 'depot'
        relationship_id = sub.id
        fuel_updated = F_Update.objects.create(sub_type=sub_type,relationship_id=relationship_id,company_id = request.user.company.id)
        fuel_updated.save()
        sub.fuel_capacity = fuel_updated
        sub.save()
        messages.success(request, 'Subsidiary Created Successfully')
        return redirect('users:stations')

    return render(request, 'users/service_stations.html', {'stations': stations})

def report_generator(request):
    if request.method == "POST":
        start_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        if request.form['report_type'] == 'Transactions':
            trans = Transaction.objects.filter(date__range=[start_date, end_date])
            requests = None; allocations = None
        if request.form['report_type'] == 'Fuel Requests':
            requests = FuelRequest.objects.filter(date_range=[start_date, end_date])
            trans = None; allocations = None
        if request.form['report_type'] == 'Allocations':
            allocations = FuelAllocation.objects.filter(date_range=[start_date, end_date])
    form = ReportForm()
    allocations = requests = trans = None

    return render(request, 'users/report.html', {'trans': trans, 'requests': requests,'allocations':allocations, 'form':form })

def depots(request):
    depots = Depot.objects.all()
    return render(request, 'users/depots.html', {'depots': depots})         


def audit_trail(request):
    trails = Audit_Trail.objects.filter(company=request.user.company).all()
    print(trails)
    return render(request, 'users/audit_trail.html', {'trails': trails})    

        

def suppliers_list(request):
    suppliers = User.objects.filter(company=request.user.company).filter(user_type='SS_SUPPLIER').all()
    for supplier in suppliers:
        subsidiary = Subsidiaries.objects.filter(id=supplier.subsidiary_id).first()
        supplier.subsidiary_name = subsidiary.name

    form1 = SupplierContactForm()         
    subsidiaries = Subsidiaries.objects.filter(is_depot=False).all()
    form1.fields['service_station'].choices = [((subsidiary.id, subsidiary.name)) for subsidiary in subsidiaries] 

    if request.method == 'POST':
        form1 = SupplierContactForm( request.POST)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone_number = request.POST.get('phone_number')
        subsidiary_id = request.POST.get('service_station')
        User.objects.create(company_position='manager',subsidiary_id=subsidiary_id,username=username, first_name=first_name, last_name=last_name, user_type = 'SS_SUPPLIER', company=request.user.company, email=email ,password=password, phone_number=phone_number)
        messages.success(request, f"{username} Registered as Service Station Rep Successfully")
        
    return render(request, 'users/suppliers_list.html', {'suppliers': suppliers, 'form1': form1})

def suppliers_delete(request, sid):
    supplier = User.objects.filter(id=sid).first()
    if request.method == 'POST':
        supplier.delete()    

    return redirect('users:suppliers_list')

def buyers_list(request):
    buyers = Profile.objects.all()
    edit_form = ProfileEditForm()
    delete_form = ActionForm()
    return render(request, 'users/buyers_list.html', {'buyers': buyers, 'edit_form': edit_form, 'delete_form': delete_form})

def buyers_delete(request, sid):
    buyer = Profile.objects.filter(id=sid).first()
    if request.method == 'POST':
        buyer.delete()    

    return redirect('users:buyers_list')


def supplier_user_delete(request,cid,sid):
    contact = SupplierContact.objects.filter(id=cid).first()
    if request.method == 'POST':
        contact.delete()

    return redirect('users:supplier_user_create', sid=sid)  

def supplier_user_create(request,sid):
    return render(request, 'users/suppliers_list.html')

def buyer_user_create(request, sid):
    return render (request, 'users/add_buyer.html') 


def edit_supplier(request,id):
    supplier = get_object_or_404(Profile, id=id)
    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=supplier)
        if form.is_valid():
            data = form.cleaned_data
            supplier = form.save()
            messages.success(request, 'Changes Successfully Updated')
            return redirect('users.index')
    else:
        form = Profile(instance=supplier)
    return render(request, 'users/supplier_edit.html', {'form': form, 'supplier': supplier})

def edit_buyer(request,id):
    buyer = get_object_or_404(Profile, id=id)
    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=buyer)
        if form.is_valid():
            data = form.cleaned_data
            buyer = form.save()
            messages.success(request, 'Changes Successfully Updated')
            return redirect('users.index')
    else:
        form = Profile(instance=supplier)
    return render(request, 'users/buyer_edit.html', {'form': form, 'buyer': buyer})

def delete_user(request,id):
    supplier = get_object_or_404(Profile, id=id)

    if request.method == 'POST':
        form = ActionForm(request.POST)
        if form.is_valid():
            supplier.delete()
            messages.success(request, 'User Has Been Deleted')
        return redirect('administrator:blog_all_posts')
    form = ActionForm()    

    return render(request, 'user/supplier_delete.html', {'form': form, 'supplier': supplier})


def depot_staff(request):
    suppliers = User.objects.filter(company=request.user.company).filter(user_type='SUPPLIER').all()
    for supplier in suppliers:
        subsidiary = Subsidiaries.objects.filter(id=supplier.subsidiary_id).first()
        supplier.subsidiary_name = subsidiary.name
    #suppliers = [sup for sup in suppliers if not sup == request.user]   
    form1 = SupplierContactForm()         
    subsidiaries = Subsidiaries.objects.filter(is_depot=True).all()
    form1.fields['service_station'].choices = [((subsidiary.id, subsidiary.name)) for subsidiary in subsidiaries] 

    if request.method == 'POST':
        form1 = SupplierContactForm( request.POST)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone_number = request.POST.get('phone_number')
        subsidiary_id = request.POST.get('service_station')
        User.objects.create(company_position='manager',subsidiary_id=subsidiary_id,username=username, first_name=first_name, last_name=last_name, user_type = 'SUPPLIER', company=request.user.company, email=email ,password=password, phone_number=phone_number)
        messages.success(request, f"{username} Registered as Depot Rep Successfully")
       
    return render(request, 'users/depot_staff.html', {'suppliers': suppliers, 'form1': form1})










