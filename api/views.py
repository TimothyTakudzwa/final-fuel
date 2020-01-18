from django.contrib import messages
from django.contrib.auth import authenticate, update_session_auth_hash
from django.core.mail import EmailMultiAlternatives
from django.core.mail.message import BadHeaderError
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from django.db.models import Q

from buyer.models import User
from company.models import FuelUpdate
from supplier.models import Subsidiaries, TokenAuthentication

import secrets
from fuelfinder import settings

user = get_user_model()


@csrf_exempt
@api_view(['POST'])
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        status = authenticate(username=username, password=password)
        if status:
            user = User.objects.get(username=username)
            if user.user_type == 'SS_SUPPLIER' and user.password_reset:
                data = {'username': user.username}
                return JsonResponse(status=201, data=data)
            elif user.user_type == 'SS_SUPPLIER':
                data = {'username': user.username}
                return JsonResponse(status=200, data=data)
            else:
                return HttpResponse(status=403)
        else:
            return HttpResponse(status=401)


@csrf_exempt
@api_view(['POST'])
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        check = User.objects.filter(username=username)
        if check.exists():
            status = authenticate(username=username, password=password)
            if status:
                user = User.objects.get(username=username)
                if user.password_reset:
                    data = {'username': user.username}
                    return JsonResponse(status=201, data=data)
                else:
                    data = {'username': user.username}
                    return JsonResponse(status=200, data=data)
            else:
                return HttpResponse(status=401)
        else:
            return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        email_check = User.objects.filter(email=email)
        username_check = User.objects.filter(username=username)

        if username_check.exists():
            return HttpResponse(status=409)
        elif email_check.exists():
            return HttpResponse(status=406)
        else:
            try:
                client = user.objects.create_user(username=username, email=email, password=password)
                client.phone_number = phone
                client.user_type = 'INDIVIDUAL'
                client.first_name = first_name
                client.last_name = last_name
                client.save()

                data = {'username': client.username}
                return JsonResponse(status=200, data=data)
            except:
                return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def update_station(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        user = User.objects.get(username=username)
        status = FuelUpdate.objects.filter(relationship_id=user.subsidiary_id)

        if status.exists():
            update = FuelUpdate.objects.get(relationship_id=user.subsidiary_id)

            p_quantity = request.POST.get('petrol_quantity')
            d_quantity = request.POST.get('diesel_quantity')
            queue = request.POST.get('queue')

            s_status = request.POST.get('status')
            limit = request.POST.get('limit')

            if update.sub_type == 'USD':
                cash = request.POST.get('cash')
                swipe = request.POST.get('swipe')

                update.cash = cash
                update.swipe = swipe
            elif update.sub_type == 'RTGS':
                swipe = request.POST.get('swipe')
                ecocash = request.POST.get('ecocash')
                cash = request.POST.get('cash')

                update.swipe = swipe
                update.ecocash = ecocash
                update.cash = cash
            elif update.sub_type == 'USD & RTGS':
                swipe = request.POST.get('swipe')
                ecocash = request.POST.get('ecocash')
                cash = request.POST.get('cash')

                update.swipe = swipe
                update.ecocash = ecocash
                update.cash = cash

            update.petrol_quantity = p_quantity
            update.diesel_quantity = d_quantity
            update.queue_length = queue
            update.status = s_status
            update.limit = limit

            update.save()

            return HttpResponse(status=200)
        else:
            return HttpResponse(status=404)


@csrf_exempt
@api_view(['POST'])
def view_station_updates(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        data = []

        user = User.objects.get(username=username)
        status = FuelUpdate.objects.filter(relationship_id=user.subsidiary_id)

        if status.exists():
            updates = FuelUpdate.objects.filter(relationship_id=user.subsidiary_id)
            for update in updates:
                company = Subsidiaries.objects.get(id=update.relationship_id)
                
                station_update = {
                    'name': company.name, 'diesel_quantity': update.diesel_quantity,
                    'diesel_price': update.diesel_price, 'petrol_quantity': update.petrol_quantity,
                    'petrol_price': update.petrol_price, 'cash': update.cash, 'ecocash': update.ecocash,
                    'swipe': update.swipe, 'usd': update.usd, 'queue': update.queue_length, 'limit': update.limit,
                    'status': update.status, 'currency_check': update.entry_type, 'diesel_usd': update.diesel_usd_price,
                    'petrol_usd': update.petrol_usd_price
                }
                data.append(station_update)
            return JsonResponse(list(data), status=200, safe=False)
        else:
            return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def view_updates_user(request):
    if request.method == 'POST':

        data = []

        sub_updates = FuelUpdate.objects.filter(sub_type='Service Station').all()
        
        for sub_update in sub_updates:
            updates = FuelUpdate.objects.filter(sub_type='Suballocation').filter(relationship_id=sub_update.relationship_id).all()
            for update in updates:
                details = Subsidiaries.objects.get(id=update.relationship_id)
                if update.diesel_quantity == 0 and update.petrol_quantity == 0:
                    pass
                else:
                    station_update = {
                        'station': details.name, 'company': details.company.name, 'queue':
                            update.queue_length, 'petrol': update.petrol_price, 'diesel': update.diesel_price,
                        'open': details.opening_time, 'close': details.closing_time, 'limit': update.limit, 'cash': update.cash,
                        'ecocash': update.ecocash, 'swipe': update.swipe, 'usd': update.usd, 'status': update.status,
                        'currency_check': update.sub_type, 'diesel_usd': update.diesel_usd_price,
                        'petrol_usd': update.petrol_usd_price
                        }
                    data.append(station_update)

        # for update in updates:
        #     details = Subsidiaries.objects.get(id=update.relationship_id)
        #     if update.diesel_quantity == 0 and update.petrol_quantity == 0:
        #         pass
        #     else:
        #         station_update = {
        #             'station': details.name, 'company': details.company.name, 'queue':
        #                 update.queue_length, 'petrol': update.petrol_price, 'diesel': update.diesel_price,
        #             'open': details.opening_time, 'close': details.closing_time, 'limit': update.limit, 'cash': update.cash,
        #             'ecocash': update.ecocash, 'swipe': update.swipe, 'usd': update.usd, 'status': update.status,
        #             'currency_check': update.sub_type, 'diesel_usd': update.diesel_usd_price,
        #             'petrol_usd': update.petrol_usd_price
        #         }
        #         data.append(station_update)

        return JsonResponse(list(data), status=200, safe=False)


@csrf_exempt
@api_view(['POST'])
def get_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        data = []

        check = User.objects.filter(username=username)
        if check.exists():
            client = User.objects.get(username=username)
            user_data = {'username': client.username, 'firstName': client.first_name,
                         'lastName': client.last_name, 'phone': client.phone_number, 'email': client.email}
            data.append(user_data)
            return JsonResponse(list(data), status=200, safe=False)
        else:
            return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def force_password_change(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        check = User.objects.filter(username=username)
        if check.exists():
            new1 = request.POST.get('new1')
            new2 = request.POST.get('new2')

            if new1 == new2:
                client = User.objects.get(username=username)
                client.set_password(new1)
                client.password_reset = False
                client.save()
                update_session_auth_hash(request, client)
                values = dict(user=client.username)
                return JsonResponse(status=200, data=values)
            else:
                return HttpResponse(status=401)
        else:
            return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def change_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        check = User.objects.filter(username=username)

        if check.exists():
            old = request.POST.get('old')
            new1 = request.POST.get('new1')
            new2 = request.POST.get('new2')

            auth = authenticate(username=username, password=old)

            if auth and (new1 == new2):
                client = User.objects.get(username=username)
                client.set_password(new1)
                client.save()
                update_session_auth_hash(request, client)
                values = dict(user=client.username)
                return JsonResponse(status=200, data=values)
            else:
                return HttpResponse(status=401)
        else:
            return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        check = User.objects.filter(email=email)
        if check.exists():
            client = User.objects.get(email=email)
            password = secrets.token_hex(3)
            client.set_password(password)
            client.password_reset = True
            client.save()
            update_session_auth_hash(request, client)

            sender = f'Fuel Finder Accounts<{settings.EMAIL_HOST_USER}>'
            title = 'Password Reset'
            message = f"Your account password was reset.Please use this password when signing in : \n" \
                      f"{password}\n" \
                      f"Remember to change the password when you sign in."

            try:
                msg = EmailMultiAlternatives(title, message, sender, [email])
                msg.send()
                return HttpResponse(200)

            except BadHeaderError:
                return HttpResponse(400)

        else:
            return HttpResponse(status=404)

