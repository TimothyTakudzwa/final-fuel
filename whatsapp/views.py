from django.shortcuts import render
from django.http import HttpResponse
from buyer.models import User
from .helper_functions import bot_action, send_message
from django.views.decorators.csrf import csrf_exempt
import json 

@csrf_exempt 
def index(request):
    response_message = ""    
    data = json.loads(request.body)
    message = data['messages'][0]['body']    
    phone_number = data['messages'][0]['author'].split('@')[0]
    if phone_number == '263718055061':
        return HttpResponse('')
    print('--------------------', message, phone_number)    
    check = User.objects.filter(phone_number = phone_number).exists()
    if check:
        user = User.objects.filter(phone_number=phone_number).first()
        if user.is_active:
            response_message = bot_action(request, user, message) 
        else:
            response_message = "Your cannot use this, please create a buyer account and then add the phone number"
    else:
        user = User.objects.create(phone_number=phone_number, stage='registration', position=1)
        response_message = bot_action(request, user, message)

    send_message(phone_number, response_message)
    return HttpResponse(response_message)
