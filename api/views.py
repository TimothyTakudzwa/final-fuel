from django.contrib.auth import authenticate, update_session_auth_hash
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model

from buyer.models import User
from company.models import FuelUpdate, Company
from supplier.models import Subsidiaries

user = get_user_model()


@csrf_exempt
@api_view(['POST'])
def login_api(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        status = authenticate(username=username, password=password)
        if status:
            user = User.objects.get(username=username)
            if user.user_type == 'SS_SUPPLIER':
                data = {'username': user.username}
                return JsonResponse(status=200, data=data)
            else:
                return HttpResponse(status=403)
        else:
            return HttpResponse(status=401)


@csrf_exempt
@api_view(['POST'])
def login_user_api(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        check = User.objects.filter(username=username)
        if check.exists():
            status = authenticate(username=username, password=password)
            if status:
                user = User.objects.get(username=username)
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
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        try:
            client = user.objects.create_user(username=username, email=email, password=password)
            client.phone_number = phone
            client.user_type = 'INDIVIDUAL'
            client.save()

            data = {'username': client.username}
            return JsonResponse(status=200, data=data)

        except:
            email_check = User.objects.filter(email=email)
            username_check = User.objects.filter(username=username)
            if username_check.exists():
                return HttpResponse(status=409)
            elif email_check.exists():
                return HttpResponse(status=406)
            else:
                return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def update_station_api(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        user = User.objects.get(username=username)
        status = FuelUpdate.objects.filter(relationship_id=user.subsidiary_id)

        if status.exists():
            update = FuelUpdate.objects.get(relationship_id=user.subsidiary_id)

            p_price = request.POST.get('petrol_price')
            d_price = request.POST.get('diesel_price')
            p_quantity = request.POST.get('petrol_quantity')
            d_quantity = request.POST.get('diesel_quantity')
            queue = request.POST.get('queue')
            payment = request.POST.get('payment_method')

            update.petrol_price = p_price
            update.diesel_price = d_price
            update.petrol_quantity = p_quantity
            update.diesel_quantity = d_quantity
            update.queue_length = queue
            update.payment_methods = payment

            update.save()

            return HttpResponse(status=200)
        else:
            return HttpResponse(status=404)


@csrf_exempt
@api_view(['POST'])
def view_station_updates_api(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        user = User.objects.get(username=username)
        status = FuelUpdate.objects.filter(relationship_id=user.subsidiary_id)

        if status.exists():
            data = FuelUpdate.objects.filter(relationship_id=user.subsidiary_id).values()
            response = list(data)
            return JsonResponse(response, status=200, safe=False)
        else:
            return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def view_updates_user_api(request):
    if request.method == 'POST':

        data = []

        updates = FuelUpdate.objects.filter()
        for update in updates:
            details = Subsidiaries.objects.get(id=update.relationship_id)
            station_update = {
                              'station': details.name, 'company': details.company.name, 'queue':
                              update.queue_length, 'petrol': update.petrol_price, 'diesel': update.diesel_price,
                              'open': details.opening_time, 'close': details.closing_time
                              }
            data.append(station_update)

        return JsonResponse(list(data), status=200, safe=False)


@csrf_exempt
@api_view(['POST'])
def change_password_api(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        user = User.objects.filter(username=username)

        if user.exists():
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
def reset_password_api(request):
    pass
