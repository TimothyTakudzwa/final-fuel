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
from users.forms import DepotContactForm
from company.models import Company, CompanyFuelUpdate
from supplier.models import Subsidiaries, SubsidiaryFuelUpdate, FuelAllocation, Transaction, Offer, DeliverySchedule
from fuelUpdates.models import SordCompanyAuditTrail
from users.models import SordActionsAuditTrail
from accounts.models import AccountHistory
from users.views import message_is_sent
from national.models import Order, NationalFuelUpdate, SordNationalAuditTrail, DepotFuelUpdate, NoicDepot

user = get_user_model()


# Create your views here.
def dashboard(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    orders = SordNationalAuditTrail.objects.filter(assigned_depot=depot).all()
    return render(request, 'noicDepot/dashboard.html', {'orders': orders})

def stock(request):
    depot = NoicDepot.objects.filter(id=request.user.subsidiary_id).first()
    depot_stock = DepotFuelUpdate.objects.filter(depot=depot).all()
    return render(request, 'noicDepot/stock.html', {'depot_stock': depot_stock, 'depot': depot})


def upload_release_note(request, id):
    allocation = SordNationalAuditTrail.objects.filter(id=id).first()
    if request.method == 'POST':
        allocation.release_date = request.POST['release_date']
        allocation.release_note = True
        allocation.save()
        messages.success(request, "Release Note Successfully created")
        return redirect('noicDepot:dashboard')


def profile(request):
    user = request.user
    return render(request, 'noicDepot/profile.html', {'user': user})
