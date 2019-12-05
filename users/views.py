import random
import locale
import tempfile


from fpdf import FPDF
# from weasyprint import HTML
from pandas import DataFrame
import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.db.models import Q
from django.shortcuts import Http404
from django.contrib.auth import authenticate, update_session_auth_hash, login, logout
from django.contrib.auth.decorators import login_required
from supplier.models import *
from supplier.forms import *
from buyer.models import *
from buyer.forms import *
from .forms import *
from .models import AuditTrail
import secrets
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from datetime import datetime, date, timedelta
from django.contrib import messages
from buyer.models import *
from supplier.forms import *
from supplier.models import *
from users.models import *
from company.models import Company
from django.contrib.auth import authenticate
from django.db.models import Q
from .forms import AllocationForm
from company.models import FuelUpdate as F_Update
from django.contrib.auth import get_user_model
user = get_user_model()


def account_activate(request):
    return render(request, 'users/account_activate.html')

@login_required()
def index(request):
    return render(request, 'users/index.html')

@login_required()
def allocate(request):
    allocates = F_Update.objects.filter(company_id=request.user.company.id).filter(~Q(sub_type='Company')).all()
    allocations = FuelAllocation.objects.all()
    company_capacity = F_Update.objects.filter(company_id=request.user.company.id).filter(sub_type='Company').first()
    if allocations is not None: 
        for alloc in allocations:
            
            subsidiary = Subsidiaries.objects.filter(id=alloc.assigned_staff_id).first()
            if subsidiary is not None:
                alloc.subsidiary_name = subsidiary.name
                #alloc.petrol_quantity= '{:,}'.format(alloc.petrol_quantity)
                #alloc.diesel_quantity= '{:,}'.format(alloc.diesel_quantity)
            else:
                allocations = allocations  
        
    else:
        allocations = allocations

    
    if allocates is not None: 
        for allocate in allocates:
            subsidiary = Subsidiaries.objects.filter(id=allocate.relationship_id).first()
            if subsidiary is not None:
                allocate.subsidiary_name = subsidiary.name
                allocate.diesel_quantity= '{:,}'.format(allocate.diesel_quantity)
                allocate.petrol_quantity= '{:,}'.format(allocate.petrol_quantity)
            else:
                allocates = allocates    
        else:
            allocates = allocates
    
    
    return render(request, 'users/allocate.html', {'allocates': allocates, 'allocations':allocations, 'company_capacity': company_capacity})

@login_required()
def allocation_update(request,id):
    if request.method == 'POST':
        if F_Update.objects.filter(id=id).exists():
            fuel_update = F_Update.objects.filter(id=id).first()
            fuel_update.petrol_quantity = fuel_update.petrol_quantity + int(request.POST['petrol_quantity'])
            fuel_update.cash = request.POST['cash']
            fuel_update.usd = request.POST['usd']
            fuel_update.swipe = request.POST['swipe']
            fuel_update.ecocash = request.POST['ecocash']
            company_quantity = F_Update.objects.filter(company_id = request.user.company.id).filter(sub_type='Company').first()
            if int(request.POST['petrol_quantity']) >= company_quantity.petrol_quantity:
                messages.warning(request, f'You can not allocate fuel above your company petrol capacity of {company_quantity.petrol_quantity}')
                return redirect('users:allocate')
            
            company_quantity.petrol_quantity = company_quantity.petrol_quantity - int(request.POST['petrol_quantity'])
            company_quantity.save()
            fuel_update.save()
            assigned_staff = user.objects.filter(subsidiary_id =fuel_update.relationship_id).first()
            FuelAllocation.objects.create(petrol_price=fuel_update.petrol_price,petrol_quantity=request.POST['petrol_quantity'],sub_type=fuel_update.sub_type,cash=request.POST['cash'],usd=request.POST['usd'],swipe=request.POST['swipe'],ecocash=request.POST['ecocash'],assigned_staff_id=assigned_staff.subsidiary_id)
            messages.success(request, 'updated petrol quantity successfully')
            service_station = Subsidiaries.objects.filter(id=fuel_update.relationship_id).first()
            reference = 'fuel allocation'
            reference_id = fuel_update.id
            action = f"You have allocated petrol quantity of {int(request.POST['petrol_quantity'])}L @ {fuel_update.petrol_price} "
            Audit_Trail.objects.create(company=request.user.company,service_station=service_station,user=request.user,action=action,reference=reference,reference_id=reference_id)
            return redirect('users:allocate')
        else:
            messages.success(request, 'Subsidiary does not exists')
            return redirect('users:allocate')
    return render(request, 'users/allocate.html')

@login_required()
def statistics(request):
    company = request.user.company
    staff_blocked = Subsidiaries.objects.filter(company=company).count() / 2
    offers = Offer.objects.filter(supplier=request.user).count()
    bulk_requests = FuelRequest.objects.filter(delivery_method="BULK").count()
    normal_requests = FuelRequest.objects.filter(delivery_method="REGULAR").count()
    staff_blocked = User.objects.filter(company=company).count()
    yesterday = date.today() - timedelta(days=1)
    #new_orders = FuelRequest.objects.filter(date__gt=yesterday)
    new_orders = 0
    clients = []
    #update = F_Update.objects.filter(company_id=company.id).first()
    diesel = 0; petrol = 0
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
    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

    revenue = round(float(sum(value)))
    revenue = '${:,.2f}'.format(revenue)
    #revenue = str(revenue) + '.00'   

    try:
        trans = Transaction.objects.all().count()/Transaction.objects.all().count()/100
    except:
        trans = 0    
    trans = str(trans) + " %"
    return render(request, 'users/statistics.html', {'staff_blocked':staff_blocked, 'offers': offers,
     'bulk_requests': bulk_requests, 'trans': trans, 'clients': clients, 'normal_requests': normal_requests,
     'diesel':diesel, 'petrol':petrol, 'revenue':revenue, 'new_orders': new_orders})

@login_required()
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

@login_required()
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

@login_required()
def stations(request):
    stations = Subsidiaries.objects.all()
    if request.method == 'POST':
        name = request.POST['name']
        address = request.POST['address']
        is_depot = request.POST['is_depot']
        opening_time = request.POST['opening_time']
        closing_time = request.POST['closing_time']
        cash = request.POST['cash']
        usd = request.POST['usd']
        swipe = request.POST['swipe']
        ecocash = request.POST['ecocash']
        sub = Subsidiaries.objects.create(company=request.user.company,name=name,address=address,is_depot=is_depot,opening_time=opening_time,closing_time=closing_time)    
        if request.POST['is_depot'] == True:
            sub_type = 'Depot'  
        else:
            sub_type = 'Service Station'
        fuel_updated = F_Update.objects.create(sub_type=sub_type,relationship_id=sub.id,company_id = request.user.company.id, cash=cash, usd=usd, swipe=swipe, ecocash=ecocash,limit=2000)
        fuel_updated.save()
        sub.fuel_capacity = fuel_updated
        sub.save()
        messages.success(request, 'Subsidiary Created Successfully')
        return redirect('users:stations')

    return render(request, 'users/service_stations.html', {'stations': stations})

@login_required()
def report_generator(request):
    form = ReportForm()
    allocations = requests = trans = None
    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        start_date = start_date.date()
        report_type = request.POST.get('report_type')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        end_date = end_date.date()
        print(f'_______________{report_type}_____________________')
        # print(f'_______________{type(start_date)}_____________________')
        # print(f'_______________{end_date}_____________________')
        if request.POST.get('report_type') == 'Transactions':
            trans = Transaction.objects.filter(date__range=[start_date, end_date])
            print(trans)
            requests = None; allocations = None
        if request.POST.get('report_type') == 'Requests':
            requests = FuelRequest.objects.filter(date__range=[start_date, end_date])
            print(f'__________________{requests}__________________________________')
            trans = None; allocations = None
        if request.POST.get('report_type') == 'Allocations':
            allocations = FuelRequest.objects.filter(date__range=[start_date, end_date])
        start = start_date
        end = end_date 
        return render(request, 'users/report.html', {'trans': trans, 'requests': requests,'allocations':allocations, 'form':form,
        'start': start, 'end': end })

    show = False

    return render(request, 'users/report.html', {'trans': trans, 'requests': requests,'allocations':allocations, 'form':form, 'show':show })

@login_required()
def export_pdf(request):
    result = ''
    if request.method == "POST":
        print(request.POST.get('type_model'))
        if request.POST.get('type_model') == "transaction":
            print('------------------Im In Here---------------------------')
            start = request.POST.get('start')
            end = request.POST.get('end')
            start = datetime.strptime(start, '%b. %d, %Y').date()
            end = datetime.strptime(end, '%b. %d, %Y').date()
            
            data = Transaction.objects.filter(date__range=[start, end])

            
            for i in data:
                result += f'Date : {i.date}\n Time : {i.time}\n Buyer : {i.buyer}\n Completed : {i.complete}\n'
            pdf = FPDF(orientation='P', format='A5')
            pdf.add_page()
            epw = pdf.w - 2*pdf.l_margin
            col_width = epw/4

            pdf.set_font('Times', '', 10)
            # pdf.image('project/static/project/img/receipt.png', x=40)
            pdf.multi_cell(w=100, h=10, txt=result)
            pdf.output(f'media/reports/transactions/Report - {datetime.now().strftime("%Y-%M-%d")}.pdf', 'F')
        if request.POST.get('type_model') == "reqs":
            print('-------------------------Im in FuelRequests----------------------')
            start = request.POST.get('start')
            end = request.POST.get('end')
            start = datetime.strptime(start, '%b. %d, %Y').date()
            end = datetime.strptime(end, '%b. %d, %Y').date()
            
            data = FuelRequest.objects.filter(date__range=[start, end])

            
            for i in data:
                result += f'Name : {i.name}\n Amount : {i.amount}\n Fuel Type : {i.fuel_type}\n Payment Method : {i.payment_method}\n'
            pdf = FPDF(orientation='P', format='A5')
            pdf.add_page()
            epw = pdf.w - 2*pdf.l_margin
            col_width = epw/4

            pdf.set_font('Times', '', 10)
            # pdf.image('project/static/project/img/receipt.png', x=40)
            pdf.multi_cell(w=100, h=10, txt=result)
            pdf.output(f'media/reports/requests/Report - {datetime.now().strftime("%Y-%M-%d")}.pdf', 'F')


        return redirect('users:report_generator')

# def generate_pdf(request):
#     if request.method == "POST":
#         print(request.POST.get('type_model'))
#         if request.POST.get('type_model') == "transaction":
#             print('------------------Im In Here---------------------------')
#             start = request.POST.get('start')
#             end = request.POST.get('end')
#             start = datetime.strptime(start, '%b. %d, %Y').date()
#             end = datetime.strptime(end, '%b. %d, %Y').date()
            
#             data = Transaction.objects.filter(date__range=[start, end])

#             # Rendered
#             html_string = render_to_string('users/report.html', {'people': people})
#             html = HTML(string=html_string)
#             result = html.write_pdf()

#             response = HttpResponse(content_type='application/pdf;')
#             response['Content-Disposition'] = 'inline; filename=list_people.pdf'
#             response['Content-Transfer-Encoding'] = 'binary'

#             with tempfile.NamedTemporaryFile(delete=True) as output:
#                 output.write(result)
#                 output.flush()
#                 output = open(output.name, 'r')
#                 response.write(output.read())

#             return response    




@login_required()
def export_csv(request):
    result = ''
    if request.method == "POST":
        print(request.POST.get('type_model'))
        if request.POST.get('type_model') == "transaction":
            print('------------------Im In Here---------------------------')
            start = request.POST.get('start')
            end = request.POST.get('end')
            start = datetime.strptime(start, '%b. %d, %Y').date()
            end = datetime.strptime(end, '%b. %d, %Y').date()
            
            data = Transaction.objects.filter(date__range=[start, end]).values()
            print(data)
            fields = ['Date', 'Time', 'Amount', 'Complete']
            #df = DataFrame(data,columns=fields)
            df = pd.DataFrame(list(data.values('date','time','buyer','complete'))) 
            #df['Date'] = f'{dt[2]}/{dt[1]}/{dt[0]}'

            day = str(datetime.now().day)
            month = str(datetime.now().month)
            year = str(datetime.now().year)

            name = 'Transactions'

            csv_name = f'{name}-{year}-{month}-{day}-ACC'
            
            if request.POST.get('format') == 'excel':
                df.to_excel(f'media/reports/transactions/csv/{csv_name}.xlsx', index=None, header=True)

                with open(f'media/reports/transactions/csv/{csv_name}.xlsx', 'rb') as csv_name:
                    response = HttpResponse(csv_name.read())
                    response['Content-Disposition'] = f'attachment;filename={name}-{day}/{month}/{year}.xlsx'
                    return response

            if request.POST.get('format') == 'csv':
                df.to_csv(f'media/reports/transactions/csv/{csv_name}.csv', index=None, header=True)

                with open(f'media/reports/transactions/csv/{csv_name}.csv', 'rb') as csv_name:
                    response = HttpResponse(csv_name.read())
                    response['Content-Disposition'] = f'attachment;filename={name}-{day}/{month}/{year}.csv'
                    return response        
                    
            



@login_required()
def depots(request):
    depots = Depot.objects.all()
    return render(request, 'users/depots.html', {'depots': depots})         

@login_required()
def audit_trail(request):
    trails = Audit_Trail.objects.filter(company=request.user.company).all()
    print(trails)
    return render(request, 'users/audit_trail.html', {'trails': trails})    

        
@login_required()
def suppliers_list(request):
    suppliers = User.objects.filter(company=request.user.company).filter(user_type='SS_SUPPLIER').all()
    if suppliers is not None:
        for supplier in suppliers:
            subsidiary = Subsidiaries.objects.filter(id=supplier.subsidiary_id).first()
            supplier.subsidiary_name = subsidiary.name
    else:
        suppliers = None

    form1 = SupplierContactForm()         
    subsidiaries = Subsidiaries.objects.filter(is_depot=False).all()
    form1.fields['service_station'].choices = [((subsidiary.id, subsidiary.name)) for subsidiary in subsidiaries] 

    if request.method == 'POST':
        form1 = SupplierContactForm( request.POST)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = 'pbkdf2_sha256$150000$fksjasjRlRRk$D1Di/BTSID8xcm6gmPlQ2tZvEUIrQHuYioM5fq6Msgs='
        phone_number = request.POST.get('phone_number')
        subsidiary_id = request.POST.get('service_station')
        User.objects.create(company_position='manager',subsidiary_id=subsidiary_id,username=username, first_name=first_name, last_name=last_name, user_type = 'SS_SUPPLIER', company=request.user.company, email=email ,password=password, phone_number=phone_number)
        messages.success(request, f"{username.capitalize()} succesfully registered as service station rep")
        return redirect('users:suppliers_list')
    
    return render(request, 'users/suppliers_list.html', {'suppliers': suppliers, 'form1': form1})

@login_required()
def suppliers_delete(request, sid):
    supplier = User.objects.filter(id=sid).first()
    if request.method == 'POST':
        supplier.delete()    
        messages.success(request, f"{supplier.username} deleted successfully")
        return redirect('users:suppliers_list')
    else:
        messages.success(request, 'user does not exists')
        return redirect('users:suppliers_list')    

@login_required()
def delete_depot_staff(request, id):
    supplier = User.objects.filter(id=id).first()
    if request.method == 'POST':
        supplier.delete()    
        messages.success(request, f"{supplier.username} deleted successfully")
        return redirect('users:depot_staff')
    else:
        messages.success(request, 'user does not exists')
        return redirect('users:depot_staff')    

@login_required()
def buyers_list(request):
    buyers = Profile.objects.all()
    edit_form = ProfileEditForm()
    delete_form = ActionForm()
    return render(request, 'users/buyers_list.html', {'buyers': buyers, 'edit_form': edit_form, 'delete_form': delete_form})

@login_required()
def buyers_delete(request, sid):
    buyer = Profile.objects.filter(id=sid).first()
    if request.method == 'POST':
        buyer.delete()    

    return redirect('users:buyers_list')

@login_required()
def supplier_user_delete(request,cid,sid):
    contact = SupplierContact.objects.filter(id=cid).first()
    if request.method == 'POST':
        contact.delete()

    return redirect('users:supplier_user_create', sid=sid)  

@login_required()
def supplier_user_create(request,sid):
    return render(request, 'users/suppliers_list.html')

@login_required()
def buyer_user_create(request, sid):
    return render (request, 'users/add_buyer.html') 

@login_required()
def edit_buyer(request,id):
    
    return render(request, 'users/buyer_edit.html', {'form': form, 'buyer': buyer})

@login_required()
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

@login_required()
def depot_staff(request):
    suppliers = User.objects.filter(company=request.user.company).filter(user_type='SUPPLIER').all()
    for supplier in suppliers:
        subsidiary = Subsidiaries.objects.filter(id=supplier.subsidiary_id).first()
        supplier.subsidiary_name = subsidiary.name
    #suppliers = [sup for sup in suppliers if not sup == request.user]   
    form1 = DepotContactForm()         
    subsidiaries = Subsidiaries.objects.filter(is_depot=True).all()
    form1.fields['depot'].choices = [((subsidiary.id, subsidiary.name)) for subsidiary in subsidiaries] 

    if request.method == 'POST':
        form1 = DepotContactForm( request.POST)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = 'pbkdf2_sha256$150000$fksjasjRlRRk$D1Di/BTSID8xcm6gmPlQ2tZvEUIrQHuYioM5fq6Msgs='
        phone_number = request.POST.get('phone_number')
        subsidiary_id = request.POST.get('depot')
        User.objects.create(company_position='manager',subsidiary_id=subsidiary_id,username=username, first_name=first_name, last_name=last_name, user_type = 'SUPPLIER', company=request.user.company, email=email ,password=password, phone_number=phone_number)
        messages.success(request, f"{username} Registered as Depot Rep Successfully")
        return redirect('users:depot_staff')
    '''
    else:
        messages.warning(request, f"The username has already been,please use another username to register")
        return redirect('users:depot_staff')
    '''
       
    return render(request, 'users/depot_staff.html', {'suppliers': suppliers, 'form1': form1})

@login_required()
def edit_subsidiary(request, id):
    if request.method == 'POST':
        if Subsidiaries.objects.filter(id=id).exists():
            subsidiary_update = Subsidiaries.objects.filter(id=id).first()
            subsidiary_update.name = request.POST['name']
            subsidiary_update.address = request.POST['address']
            subsidiary_update.is_depot = request.POST['is_depot']
            subsidiary_update.opening_time = request.POST['opening_time']
            subsidiary_update.closing_time = request.POST['closing_time']
            subsidiary_update.save()
            messages.success(request, 'Subsidiary updated successfully')
            reference = 'subsidiary profile update'
            reference_id = subsidiary_update.id
            action = f"You have updated the profile of {subsidiary_update.name}"
            Audit_Trail.objects.create(company=request.user.company,service_station=subsidiary_update,user=request.user,action=action,reference=reference,reference_id=reference_id)
            return redirect('users:stations')
        else:
            messages.success(request, 'Subsidiary does not exists')
            return redirect('users:stations')

@login_required()
def delete_subsidiary(request, id):
    if request.method == 'POST':
        if Subsidiaries.objects.filter(id=id).exists():
            subsidiary_update = Subsidiaries.objects.filter(id=id).first()
            subsidiary_update.delete()
            messages.success(request, 'Subsidiary deleted successfully')
            return redirect('users:stations')

        else:
            messages.success(request, 'Subsidiary does not exists')
            return redirect('users:stations')    

@login_required()
def edit_fuel_prices(request, id):
    if request.method == 'POST':
        if F_Update.objects.filter(id=id).exists():
            prices_update = F_Update.objects.filter(id=id).first()
            prices_update.petrol_price = request.POST['petrol_price']
            prices_update.diesel_price = request.POST['diesel_price']
            prices_update.save()
            messages.success(request, 'Prices of fuel updated successfully')
            service_station = Subsidiaries.objects.filter(id=prices_update.relationship_id).first()
            reference = 'prices updates'
            reference_id = prices_update.id
            action = f"You have changed petrol price to {request.POST['petrol_price']} and diesel price to {request.POST['diesel_price']} "
            Audit_Trail.objects.create(company=request.user.company,service_station=service_station,user=request.user,action=action,reference=reference,reference_id=reference_id)
            return redirect('users:allocate')

        else:
            messages.success(request, 'Fuel object does not exists')
            return redirect('users:allocate')    


@login_required()
def allocate_diesel(request, id):
    if request.method == 'POST':
        if F_Update.objects.filter(id=id).exists():
            diesel_update = F_Update.objects.filter(id=id).first()
            diesel_update.diesel_quantity = diesel_update.diesel_quantity + int(request.POST['diesel_quantity'])
            company_quantity = F_Update.objects.filter(company_id = request.user.company.id).filter(sub_type='Company').first()
            if int(request.POST['diesel_quantity']) >= company_quantity.diesel_quantity:
                messages.warning(request, f'You can not allocate fuel above your company diesel capacity of {company_quantity.diesel_quantity}')
                return redirect('users:allocate')
            
            company_quantity.diesel_quantity = company_quantity.diesel_quantity - int(request.POST['diesel_quantity'])
            company_quantity.save()
            diesel_update.save()
            assigned_staff = user.objects.filter(subsidiary_id =diesel_update.relationship_id).first()
            FuelAllocation.objects.create(diesel_price=diesel_update.diesel_price,diesel_quantity=request.POST['diesel_quantity'],sub_type=diesel_update.sub_type,cash=request.POST['cash'],usd=request.POST['usd'],swipe=request.POST['swipe'],ecocash=request.POST['ecocash'],assigned_staff_id=assigned_staff.subsidiary_id)
            messages.success(request, 'Updated diesel quantity successfully')
            service_station = Subsidiaries.objects.filter(id=diesel_update.relationship_id).first()
            reference = 'fuel allocation'
            reference_id = diesel_update.id
            action = f"You have allocated diesel quantity of {int(request.POST['diesel_quantity'])}L @ {diesel_update.diesel_price} "
            Audit_Trail.objects.create(company=request.user.company,service_station=service_station,user=request.user,action=action,reference=reference,reference_id=reference_id)
            return redirect('users:allocate')

        else:
            messages.success(request, 'Fuel object does not exists')
            return redirect('users:allocate')    

@login_required()
def edit_ss_rep(request, id):
    if request.method == 'POST':
        if user.objects.filter(id=id).exists():
            user_update = user.objects.filter(id=id).first()
            user_update.phone_number = request.POST['phone_number']
            user_update.save()
            messages.success(request, 'User profile updated successfully')
            return redirect('users:suppliers_list')

        else:
            messages.success(request, 'user does not exists')
            return redirect('users:suppliers_list')    

@login_required()
def edit_depot_rep(request, id):
    if request.method == 'POST':
        if user.objects.filter(id=id).exists():
            user_update = user.objects.filter(id=id).first()
            user_update.phone_number = request.POST['phone_number']
            user_update.save()
            messages.success(request, 'User profile updated successfully')
            return redirect('users:depot_staff')

        else:
            messages.success(request, 'user does not exists')
            return redirect('users:depot_staff')    

def company_profile(request):
    compan = Company.objects.filter(id = request.user.company.id).first()
    num_of_subsidiaries = Subsidiaries.objects.filter(company=request.user.company).count()
    fuel_capacity = F_Update.objects.filter(sub_type='Company').first()
    return render(request, 'users/company_profile.html', {'compan': compan, 'num_of_subsidiaries': num_of_subsidiaries, 'fuel_capacity': fuel_capacity})

def company_petrol(request,id):
    if request.method == 'POST':
        if F_Update.objects.filter(id=id).exists():
            petrol_update = F_Update.objects.filter(id=id).first()
            petrol_update.petrol_price = request.POST['petrol_price']
            petrol_update.petrol_quantity = request.POST['petrol_quantity']
            petrol_update.save()
            messages.success(request, 'Quantity of petrol updated successfully')
            return redirect('users:allocate')

        else:
            messages.success(request, 'Fuel object does not exists')
            return redirect('users:allocate')    

def company_diesel(request,id):
    if request.method == 'POST':
        if F_Update.objects.filter(id=id).exists():
            diesel_update = F_Update.objects.filter(id=id).first()
            diesel_update.diesel_quantity = request.POST['diesel_quantity']
            diesel_update.diesel_price = request.POST['diesel_price']
            diesel_update.save()
            messages.success(request, 'Quantity of diesel updated successfully')
            return redirect('users:allocate')

        else:
            messages.success(request, 'Fuel object does not exists')
            return redirect('users:allocate') 




