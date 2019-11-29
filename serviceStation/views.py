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
from buyer.models import User
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
user = get_user_model()


def fuel_updates(request):
    updates = FuelUpdate.objects.all()
    if request.method == 'POST':
        if FuelUpdate.objects.filter(fuel_type=request.POST['fuel_type']).exists():
            fuel_update = FuelUpdate.objects.get(fuel_type=request.POST['fuel_type'])
            fuel_update.available_quantity = request.POST['available_quantity']
            fuel_update.price = request.POST['price']
            fuel_update.payment_method = request.POST['payment_method']
            fuel_update.queue_size = request.POST['queue_size']
            fuel_update.status = request.POST['status']
            fuel_update.save()
            messages.success(request, 'updated quantity successfully')
            return redirect('serviceStation:serviceStation')
        else:
            available_quantity = request.POST.get('available_quantity')
            price = request.POST.get('price')
            status = request.POST.get('status')
            #queue_size = request.POST.get('queue_size')
            fuel_type = request.POST.get('fuel_type')
            payment_method = request.POST.get('payment_method')
            supplier = request.user
            FuelUpdate.objects.create(supplier=supplier, payment_method=payment_method, fuel_type=fuel_type, available_quantity=available_quantity, price=price, status=status)
            messages.success(request, 'Quantity uploaded successfully')
            return redirect('serviceStation:serviceStation')

    return render(request, 'serviceStation/fuel_updates.html', {'updates': updates})


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