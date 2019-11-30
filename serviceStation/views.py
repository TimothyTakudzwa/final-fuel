from django.shortcuts import render, get_object_or_404, redirect
import secrets
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from datetime import datetime
from django.contrib import messages
from buyer.models import User, Company
from django.contrib.auth import authenticate
from supplier.forms import UserUpdateForm
from .forms import ProfileUdateForm
from supplier.forms import *
from supplier.models import *
from company.models import FuelUpdate
from buyer~.models import User
from users.models import Audit_Trail
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
user = get_user_model()


def fuel_updates(request):
    print(f"--------------------------{request.user.subsidiary_id}----------------------")

    updates = FuelUpdate.objects.filter(sub_type='service_station').filter(relationship_id=request.user.subsidiary_id).first()
    subsidiary_name = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
    print(f"--------------------------{updates}----------------------")
    if request.method == 'POST':
        if FuelUpdate.objects.filter(sub_type=request.POST['sub_type']).exists():
            fuel_update = FuelUpdate.objects.get(sub_type=request.POST['sub_type'])
            fuel_update.petrol_quantity = request.POST['petrol_quantity']
            fuel_update.petrol_price = request.POST['petrol_price']
            fuel_update.diesel_quantity = request.POST['diesel_quantity']
            fuel_update.diesel_price = request.POST['diesel_price']
            fuel_update.payment_methods = request.POST['payment_methods']
            fuel_update.queue_length = request.POST['queue_length']
            fuel_update.save()
            messages.success(request, 'updated quantities successfully')
            service_station = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
            reference = 'fuel quantity updates'
            reference_id = fuel_update.id
            action = f"{request.user.username} has made an update of diesel quantity to {fuel_update.diesel_quantity} @ {fuel_update.diesel_price} and petrol quantity to {fuel_update.petrol_quantity} @ {fuel_update.petrol_price}"
            Audit_Trail.objects.create(company=request.user.company,service_station=service_station,user=request.user,action=action,reference=reference,reference_id=reference_id)
            return redirect('serviceStation:home')
        else:
            sub_type = request.POST.get('sub_type')
            petrol_quantity = request.POST.get('petrol_quantity')
            petrol_price = request.POST.get('petrol_price')
            diesel_quantity = request.POST.get('diesel_quantity')
            diesel_price = request.POST.get('diesel_price')
            payment_methods = request.POST.get('payment_methods')
            queue_length = request.POST.get('queue_length')
            relationship_id = request.user.subsidiary_id
            FuelUpdate.objects.create(relationship_id=relationship_id, sub_type=sub_type,payment_methods=payment_methods,queue_length=queue_length, petrol_quantity=petrol_quantity, petrol_price=petrol_price, diesel_quantity=diesel_quantity, diesel_price=diesel_price)
            messages.success(request, 'Quantities uploaded successfully')
            return redirect('serviceStation:home')

    return render(request, 'serviceStation/fuel_updates.html', {'updates': updates, 'subsidiary': subsidiary_name.name})


def allocated_fuel(request):
    allocates = FuelAllocation.objects.filter(assigned_staff = request.user).all()
    return render(request, 'serviceStation/allocated_fuel.html', {'allocates': allocates})


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

'''
def user_profile(request):
    user = User.objects.filter(name=request.name)
    if request.method == 'POST':
        form = ProfileUdateForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            form = ProfileUdateForm()

    else:
        form = ProfileUdateForm()
    return render(request, 'serviceStation/userprofile.html', {'user': user})

'''