from django.shortcuts import render, get_object_or_404, redirect
import secrets
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, update_session_auth_hash, login, logout
from datetime import datetime
from django.contrib import messages
from buyer.models import User, Company
from django.contrib.auth import authenticate
from supplier.forms import UserUpdateForm, PostForm
from .forms import ProfileUdateForm
from supplier.forms import *
from supplier.models import *
from company.models import FuelUpdate
from buyer.models import User
from users.models import Audit_Trail
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
user = get_user_model()

@login_required()
def fuel_updates(request):
    updates = FuelUpdate.objects.filter(relationship_id=request.user.subsidiary_id).filter(sub_type='Suballocation').order_by('-entry_type').all()
    subsidiary_name = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
    if request.method == 'POST':
        #fuel_update = FuelUpdate.objects.filter(sub_type=request.POST['sub_type']).first()
        if int(updates.petrol_quantity) < int(request.POST['petrol_quantity']):
            messages.warning(request, 'You cannot update Petrol to an amount more than the available quantity')
            return redirect('serviceStation:home')
        updates.petrol_quantity = request.POST['petrol_quantity'] 
        updates.queue_length = request.POST['queue_length']
        updates.status = request.POST['status']
        
        if int(updates.petrol_quantity) < 1000:
            updates.status = 'Expecting Fuel'
            updates.save()
            messages.warning(request, 'Please request for more fuel from you Company')
            return redirect('serviceStation:home')

        updates.save()
        messages.success(request, 'Updated Petrol QuantitY Successfully')
        service_station = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
        reference = 'fuel quantity updates'
        reference_id = updates.id
        action = f"{request.user.username} has made an update of petrol quantity to {updates.petrol_quantity}L @ {updates.petrol_price}"
        Audit_Trail.objects.create(company=request.user.company,service_station=service_station,user=request.user,action=action,reference=reference,reference_id=reference_id)
        return redirect('serviceStation:home')

    return render(request, 'serviceStation/fuel_updates.html', {'updates': updates, 'subsidiary': subsidiary_name.name})


def station_fuel_update(request,id):
    if request.method == 'POST':
        if FuelUpdate.objects.filter(id=id).exists():
            fuel_update = FuelUpdate.objects.filter(id=id).first()
            if request.POST['fuel_type'] == 'Petrol':
                if int(request.POST['quantity']) > fuel_update.petrol_quantity:
                    messages.warning(request, f'You can not update fuel to an amount above your current petrol quantity of {fuel_update.petrol_quantity}')
                    return redirect('serviceStation:home')
                fuel_update.petrol_quantity = int(request.POST['quantity']) 
                fuel_update.queue_length = request.POST['queue_length']
                fuel_update.status = request.POST['status']
                fuel_update.save()
                messages.success(request, 'Fuel update made successfully')
                return redirect('serviceStation:home')
            else:
                if int(request.POST['quantity']) > fuel_update.diesel_quantity:
                    messages.warning(request, f'You can not update fuel to an amount above your current diesel quantity of {fuel_update.diesel_quantity}')
                    return redirect('serviceStation:home')
                fuel_update.diesel_quantity = int(request.POST['quantity']) 
                fuel_update.queue_length = request.POST['queue_length']
                fuel_update.status = request.POST['status']
                fuel_update.save()
                messages.success(request, 'Fuel update made successfully')
                return redirect('serviceStation:home')

@login_required()
def update_diesel(request, id):
    if request.method == 'POST':
        diesel_update = FuelUpdate.objects.filter(id=id).first()
        if int(diesel_update.diesel_quantity) < int(request.POST['diesel_quantity']):
            messages.warning(request, 'You cannot update Diesel to an amount more than the available quantity')
            return redirect('serviceStation:home')
        diesel_update.diesel_quantity = request.POST['diesel_quantity']
        diesel_update.queue_length = request.POST['queue_length']
        diesel_update.status = request.POST['status']
       
        if int(diesel_update.diesel_quantity) < 1000:
            diesel_update.status = 'Expecting Fuel'
            diesel_update.save()
            messages.warning(request, 'Please request for more fuel from you Company')
            return redirect('serviceStation:home')

        diesel_update.save()
        messages.success(request, 'Updated Diesel QuantitY Successfully')
        service_station = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
        reference = 'fuel quantity updates'
        reference_id = diesel_update.id
        action = f"{request.user.username} has made an update of diesel quantity to {diesel_update.diesel_quantity}L @ {diesel_update.diesel_price}"
        Audit_Trail.objects.create(company=request.user.company,service_station=service_station,user=request.user,action=action,reference=reference,reference_id=reference_id)
        return redirect('serviceStation:home')

    else:
        messages.success(request, 'Fuel Object Does Not Exist')
        return redirect('serviceStation:home')


@login_required()
def allocated_fuel(request):
    allocates = FuelAllocation.objects.filter(assigned_staff = request.user).all()
    return render(request, 'serviceStation/allocated_fuel.html', {'allocates': allocates})

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
       
    return render(request, 'serviceStation/profile.html')


#activated_for_whatsapp
def activate_whatsapp(request):
    usr = user.objects.filter(id=request.user.id).first()
    if usr.activated_for_whatsapp == False:
        usr.activated_for_whatsapp = True
        usr.save()
        messages.success(request, 'Your WhatsApp has been activated successfully')
        return redirect('serviceStation:home')

    else:
        usr.activated_for_whatsapp = False
        usr.save()
        messages.warning(request, 'Your WhatsApp has been deactivated successfully')
        return redirect('serviceStation:home')

def allocated_quantity(request):
    allocations = FuelAllocation.objects.filter(allocated_subsidiary_id= request.user.subsidiary_id).all()
    return render(request, 'serviceStation/allocated_quantity.html', {'allocations': allocations})


def subsidiary_profile(request):
    subsidiary = Subsidiaries.objects.filter(id = request.user.subsidiary_id).first()
    fuel_capacity = FuelUpdate.objects.filter(relationship_id=subsidiary.id).first()
    form = PostForm()

    if request.method == 'POST':
        if FuelUpdate.objects.filter(id=fuel_capacity.id).exists():
            fuel_update = FuelUpdate.objects.filter(id=fuel_capacity.id).first()
            fuel_update.petrol_quantity = request.POST['petrol']
            fuel_update.diesel_quantity = request.POST['diesel']
            fuel_update.save()
            subsidiary.name = request.POST['name']
            subsidiary.company = request.POST['company']
            subsidiary.address = request.POST['address']
            subsidiary.iban_number = request.POST['iban_number']
            subsidiary.licence_number = request.POST['licence_number']
            subsidiary.destination_bank = request.POST['destination_bank']
            subsidiary.account_number = request.POST['account_number']
            subsidiary.save()
            messages.success(request, 'Service Station Profile updated successfully')
            return redirect('serviceStation:subsidiary_profile')

        else:
            messages.success(request, 'Something went wrong')
            return redirect('serviceStation:subsidiary_profile')    
    return render(request, 'serviceStation/subsidiary_profile.html', {'subsidiary': subsidiary, 'fuel_capacity': fuel_capacity,'form': form})

def logo_upload(request, id):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES) 
        subsidiary = Subsidiaries.objects.filter(id = id).first()
        print(id)
        subsidiary.logo = request.POST['logo']
        subsidiary.save()
        messages.success(request, 'Logo updated successfully')
        return redirect('serviceStation:subsidiary_profile')
 
    else: 
        form = PostForm() 
    return redirect('serviceStation:subsidiary_profile')

def edit_password(request):
    context = {
        'title': 'Fuel Finder | Change Password',
        'password_change': PasswordChange(user=request.user)
    }
    if request.method == 'POST':
        old = request.POST.get('old_password')
        new1 = request.POST.get('new_password1')
        new2 = request.POST.get('new_password2')

        if authenticate(request, username=request.user.username, password=old):
            if new1 != new2:
                messages.warning(request, "Passwords Don't Match")
                return redirect('serviceStation:edit_password')
            elif new1 == old:
                messages.warning(request, "New password can not be similar to the old one")
                return redirect('serviceStation:edit_password')
            elif len(new1) < 8:
                messages.warning(request, "Password is too short")
                return redirect('serviceStation:edit_password')
            elif new1.isnumeric():
                messages.warning(request, "Password can not be entirely numeric!")
                return redirect('serviceStation:edit_password')
            elif not new1.isalnum():
                messages.warning(request, "Password should be alphanumeric")
                return redirect('serviceStation:edit_password')
            else:
                user = request.user
                user.set_password(new1)
                user.save()
                update_session_auth_hash(request, user)

                messages.success(request, 'Password Successfully Changed')
                return redirect('serviceStation:myaccount')
        else:
            messages.warning(request, 'Wrong Old Password, Please Try Again')
            return redirect('serviceStation:edit_password')
    return render(request, 'serviceStation/change_password.html', context=context)
  