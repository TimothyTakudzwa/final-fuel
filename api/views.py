from django.contrib.auth import authenticate
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render
from buyer.models import User


def login_api(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        status = authenticate(username=username, password=password)
        if status:
            user = User.objects.get(username=username)
            data = {'username': user.username}
            return JsonResponse(status=200, data=data)
        else:
            return HttpResponse(status=401)


def update_station_api(request):
    pass


def view_station_updates_api(request):
    pass


def logout_api(request):
    pass
