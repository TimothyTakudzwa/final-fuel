import json

from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

from buyer.models import User
from .helper_functions import bot_action, send_message



@csrf_exempt 
def index(request):
    response_message = ""    
    data = json.loads(request.body)
    message = data['messages'][0]['body']    
    phone_number = data['messages'][0]['author'].split('@')[0]
    if phone_number == '263718055061':
        return HttpResponse('')
    check = User.objects.filter(phone_number = phone_number).exists()
        if check:
    user = User.objects.filter(phone_number=phone_number).first()
    print('--------------------', message, phone_number, user.stage, user.position)    

    if user.is_active:
        response_message = bot_action(request, user, message) 
    else:
        response_message = "Your cannot use this, please create a buyer account or wait for approval if you have already registered"
else:
user = User.objects.create(phone_number=phone_number, stage='registration', position=1)
response_message = bot_action(request, user, message)

a send_message(phone_number, response_message)
return HttpResponse(response_message)
