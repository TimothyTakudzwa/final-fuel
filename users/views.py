import random

from django.shortcuts import render, get_object_or_404, redirect

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
from company.models import FuelUpdate as fex
from django.contrib.auth import get_user_model
user = get_user_model()


def index(request):
    return render(request, 'users/index.html')


def allocate(request):
    allocates = fex.objects.all()
    
    if request.method == 'POST':
        if fex.objects.filter(id= int(request.POST['id'])).exists():
            fuel_update = fex.objects.filter(id= int(request.POST['id'])).first()
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

    staff_blocked = SupplierContact.objects.count()
    offers = Offer.objects.count()
    bulk_requests = FuelRequest.objects.filter(delivery_method="Bulk").count()
    staff_blocked = len(User.objects.all())
    clients = []
    companies = Company.objects.filter(company_type='Corporate')
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
     'bulk_requests': bulk_requests, 'trans': trans, 'clients': clients})


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
        Subsidiaries.objects.create(company=request.user.company,name=name,address=address,is_depot=is_depot,opening_time=opening_time,closing_time=closing_time)
        messages.success(request, 'Subsidiary Created Successfully')
        return redirect('users:stations')

    return render(request, 'users/service_stations.html', {'stations': stations})

def report_generator(request):
   
    if request.method == "POST":
        
        form = ReportForm(request.POST or None)
        if form.is_valid():
            end_date = form.cleaned_data.get('end_date')
            start_date = form.cleaned_data.get('start_date')
            
            # start_date = datetime.strptime(str(start_date), '%Y-%m-%d')
            # end_date = datetime.strptime(str(end_date), '%Y-%m-%d')
            if form.cleaned_data.get('report_type') == 'Transactions':
                trans = Transaction.objects.filter(date__range=[start_date, end_date])
                requests = None; allocations = None
            if form.cleaned_data.get('report_type') == 'Fuel Requests':
                requests = FuelRequest.objects.filter(date__range=[start_date, end_date])
                trans = None; allocations = None
            if form.cleaned_data.get('report_type') == 'Allocations':
                allocations = FuelAllocation.objects.filter(date__range=[start_date, end_date])
            return render(request, 'users/report.html', {'trans': trans, 'requests': requests,'allocations':allocations, 'form':form } )
        else:
            messages.success(request, f"Suo")       

        allocations = requests = trans = None
    form = ReportForm()
    allocations = requests = trans = None

    return render(request, 'users/report.html', {'trans': trans, 'requests': requests,'allocations':allocations, 'form':form } )

def depots(request):
    stations = Subsidiaries.objects.filter(company.id == request.user.company.id).first()
    return render(request, 'users/depots.html', {'depots': depots})         


def audit_trail(request):
    trails = Audit_Trail.objects.all()
    print(trails)
    return render(request, 'users/audit_trail.html', {'trails': trails})    

        

def suppliers_list(request):
    suppliers = User.objects.filter(company=request.user.company).all()  
    form1 = SupplierContactForm()         
    companies = Company.objects.all()
    form1.fields['service_station'].choices = [((company.id, company.name)) for company in companies] 

    if request.method == 'POST':
        form1 = SupplierContactForm( request.POST)
        
        print('--------------------tapinda---------------')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('paasword')
        phone_number = request.POST.get('phone_number')
        supplier_role = 'Staff'
        f_service_station = request.POST.get('service_station')
        company = Company.objects.get(id=f_service_station)
        
        print(type(User))
        User.objects.create(username=username, first_name=first_name, last_name=last_name, user_type = 'SUPPLIER', company=company, email=email ,password=password, phone_number=phone_number,supplier_role=supplier_role)
        messages.success(request, f"{username} Registered Successfully")
        '''
        token = secrets.token_hex(12)
        user = User.objects.get(username=username)
        TokenAuthentication.objects.create(token=token, user=user)
        domain = request.get_host()
        url = f'{domain}/verification/{token}/{user.id}' 

        sender = f'Fuel Finder Accounts<tests@marlvinzw.me>'
        subject = 'User Registration'
        message = f"Dear {username} , please complete signup here : \n {url} \n. Your password is {password}"
        
        try:
            msg = EmailMultiAlternatives(subject, message, sender, [f'{email}'])
            msg.send()

            except BadHeaderError:
                messages.warning(request, f"Oops , Something Wen't Wrong, Please Try Again")
                return redirect('users:buyers_list')
            #contact.save()
            messages.success(request, ('Your profile was successfully updated!'))
            return redirect('users:suppliers')
            print(token)
            print("above is the token")
            '''
    else:
        form1 = SupplierContactForm()  
        service_stations = Subsidiaries.objects.filter(company = request.user.company).all() 
        form1.fields['service_station'].choices = [(service_station.id, service_station.name) for service_station in service_stations] 
        return render(request, 'users/suppliers_list.html', {'suppliers': suppliers,'form1': form1})
    return render(request, 'users/suppliers_list.html', {'suppliers': suppliers,'form1': form1})

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

# Begining Of Supplier Management

def supplier_user_create(request,sid):
    return render(request, 'users/suppliers_list.html')



def buyer_user_create(request, sid):
    buyer = get_object_or_404(Profile, id=sid) 
    staff = BuyerContact.objects.filter(buyer_profile=buyer)
    count = BuyerContact.objects.all().count()
    delete_form = ''
    edit_form = ''
    if request.method == 'POST':
        user_count = BuyerContact.objects.filter(buyer_profile=buyer).count()
        if user_count > 10:
            raise Http404("Your organisation has reached the maximum number of users, delete some ")
        form = BuyerContactForm(request.POST)
        profile_form = UserUpdateForm(request.POST, instance=buyer)

        if profile_form.is_valid():
            buyer = profile_form.save()
            messages.success(request, 'Your Changes Have Been Saved')
            return redirect('users:buyer_user_create', sid=buyer.id)

        

        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            cellphone = form.cleaned_data['phone']
            user = User.objects.create_user(first_name, email, password)
            user.last_name = form.cleaned_data['last_name']
            user.first_name = form.cleaned_data['first_name']
            user.save()   
            contact = BuyerContact.objects.create(user=user, phone=cellphone, buyer_profile=buyer)

            token = secrets.token_hex(12)
            user = User.objects.get(first_name=first_name)
            TokenAuthentication.objects.create(token=token, user=user)
            domain = request.get_host()
            url = f'{domain}/verification/{token}/{user.id}' 

            sender = f'Fuel Finder Accounts<tests@marlvinzw.me>'
            subject = 'User Registration'
            message = f"Dear {first_name} , please complete signup here : \n {url} \n. Your password is {password}"
            
            try:
                msg = EmailMultiAlternatives(subject, message, sender, [f'{email}'])
                msg.send()

                messages.success(request, f"{first_name} Registered Successfully")
                return redirect('users:buyers_list')

            except BadHeaderError:
                messages.warning(request, f"Oops , Something Wen't Wrong, Please Try Again")
                return redirect('users:buyers_list')
            #contact.save()
            messages.success(request, ('Your profile was successfully updated!'))
            return redirect('users:buyer_user_create', sid=buyer.id)
            print(token)
            print("above is the token")

        else:
            msg = "Error in Information Submitted"
            messages.error(request, msg)
    else:
        form = BuyerContactForm()
        profile_form = UserUpdateForm(instance=buyer)



    return render (request, 'users/add_buyer.html', {'form': form, 'buyer': buyer, 'staff': staff, 'count': count, 'delete_form':delete_form, 'edit_form': edit_form, 'profile_form':profile_form}) 


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
    suppliers = User.objects.filter(company=request.user.company)  
    form1 = SupplierContactForm()         
    #companies = Company.objects.all()
    #form1.fields['service_tation'].choices = [((company.id, company.name)) for company in companies] 

    if request.method == 'POST':
        form1 = SupplierContactForm( request.POST)
        
        print('--------------------tapinda---------------')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('paasword')
        phone_number = request.POST.get('phone_number')
        supplier_role = 'Staff'
        f_service_station = request.POST.get('service_station')
        company = Company.objects.get(id=f_service_station)
        
        print(type(User))
        User.objects.create(username=username, first_name=first_name, last_name=last_name, user_type = 'SUPPLIER', company=company, email=email ,password=password, phone_number=phone_number,supplier_role=supplier_role)
        messages.success(request, f"{username} Registered Successfully")
        '''
        token = secrets.token_hex(12)
        user = User.objects.get(username=username)
        TokenAuthentication.objects.create(token=token, user=user)
        domain = request.get_host()
        url = f'{domain}/verification/{token}/{user.id}' 

        sender = f'Fuel Finder Accounts<tests@marlvinzw.me>'
        subject = 'User Registration'
        message = f"Dear {username} , please complete signup here : \n {url} \n. Your password is {password}"
        
        try:
            msg = EmailMultiAlternatives(subject, message, sender, [f'{email}'])
            msg.send()

            messages.success(request, f"{username} Registered Successfully")
            return redirect('users:buyers_list')

        except BadHeaderError:
            messages.warning(request, f"Oops , Something Wen't Wrong, Please Try Again")
            return redirect('users:buyers_list')
        #contact.save()
        messages.success(request, ('Your profile was successfully updated!'))
        return redirect('users:suppliers')
        print(token)
        print("above is the token")
        '''
    
    return render(request, 'users/depot_staff.html', {'suppliers': suppliers, 'form1': form1})










