from django.shortcuts import render
import requests
from validate_email import validate_email
from .constants import *
from buyer.views import token_is_send
from supplier.models import FuelRequest, Offer, Transaction
# from finder.reccomend import recommend
# from django.core.validators import validate_email
from buyer.models import User


def send_message(phone_number, message):
    payload = {
        "phone": phone_number,
        "body": message
    }
    url = "https://eu33.chat-api.com/instance78632/sendMessage?token=sq0pk8hw4iclh42b"
    r = requests.post(url=url, data=payload)
    print(r)
    return r.status_code

def individual_handler(request, user,message):
    if message.lower() == 'menu' and user.stage != 'registration':
        user.position = 1
        user.stage = 'requesting'
        user.save()
        return requests_handler(user, message)
    pass

def buyer_handler(request,user,message):
    if message.lower() == 'menu' and user.stage != 'registration':
        user.position = 1
        user.stage = 'requesting'
        user.save()
        return requests_handler(user, message)
    pass 

def supplier_handler(request,user,message):
    if message.lower() == 'menu' and user.stage != 'registration':
        user.position = 1
        user.stage = 'requesting'
        user.save()
        return requests_handler(user, message)
    pass

def service_station_handler(request,user,message):
    if message.lower() == 'menu' and user.stage != 'registration':
        user.position = 1
        user.stage = 'requesting'
        user.save()
        return requests_handler(user, message)
    pass


def bot_action(request, user, message):   
    if user.stage == 'registration':
        return registration_handler(request, user, message)
    if user.user_type == 'INDIVIDUAL':
        return individual_handler(request, user, message)
        
    elif user.user_type == 'S_ADMIN':
        return "You are not allowed to use this platform"
    elif user.user_type == 'BUYER':
        return buyer_handler(request, user,message)
    elif user.user_type == 'SUPPLIER':
        return supplier_handler(requests_handler, user, message)
    elif user.user_type == 'SS_SUPPLIER':
        return service_station_handler(request, user,message)    
    return response_message


def registration_handler(request, user, message):
    if user.position == 1:
        response_message = "First before we get started can i please have your *Full Name*"
        user.position = 2 
        user.save()
    elif user.position == 2:        
        try:
            user.first_name, user.last_name = message.split(' ', 2)[0], message.split(' ', 2)[1]
        except:
            user.first_name = message 
        full_name = user.first_name + " " + user.last_name
        response_message = greetings_message.format(full_name)
        user.position = 3    
        user.save()
    elif user.position == 3:         
        try: 
            selected_option = user_types[int(message)-1]
            user.user_type = selected_option
            user.position = 4
            user.save()
        except:
            return "Please select a valid option\n\n" + greetings_message
        if selected_option == 'supplier' or selected_option == 'buyer':
            response_message = "Can i have your company email address.\n*NB* using your personal email address gets you lower precedence in the fuel finding process"
        else:
            response_message = "Can i please have your email address"   
    elif user.position == 4:              
        is_valid = validate_email(message, verify=True)        
        if is_valid is None:           
            pass
        else: 
            return "*_This email does not exist_*.\n\nPlease enter the a valid email address"  
        user.email = message.lower()
        if user.user_type == 'individual':
            user.stage = 'individual_finder'
            user.position = 1
            user.save()
            return "You have finished the registration process for Fuel Finder. To now start looking for fuel, Please type *Pakaipa*" 
        else:
            user.position = 4 
            user.save()
            if user.last_name != '':
                username = initial_username = user.first_name[0] + user.last_name 
            else:
                 username = initial_username = user.first_name[0] + user.first_name
            i = 0
            while User.objects.filter(username=username.lower()).exists():
                username = initial_username + str(i)  
            user.username = username.lower()          
            if token_is_send(request, user):
                response_message = "We have sent a verification email to your supplied email, Please visit the link to complete the registration process"
                user.is_active = True
                user.save()
            else:
                response_message = "*_We have failed to register you to the platform_*.\n\nPlease enter a valid email address"
                user.position = 3
                user.save()
    elif user.position == 4:
        user.user_type = 'Supplier' if message == "1" else "Buyer"
        
    return response_message


def requests_handler(user, message):    
    if user.position == 1:
        response_message = "Which type of fuel do you want\n\n1. Petrol\n2. Diesel"
        user.position = 3
        user.save()
    elif user.position == 3:
        response_message = "How many litres do you want?"
        fuel_type = "Petrol" if message == '1' else "Diesel"
        fuel_request = FuelRequest.objects.create(fuel_type=fuel_type, name=user.name)
        user.fuel_request = fuel_request
        user.position = 4
        user.save()
    elif user.position == 4:
        fuel_request = FuelRequest.objects.get(id=user.fuel_request.id)
        fuel_request.amount = message
        fuel_request.save()
        user.position = 5
        user.save()
        response_message = "*Please select delivery method*\n\n1. Pick Up\n2. Delivery"       
    elif user.position == 5: 
        delivery_method = "SELF COLLECTION" if message == '1' else "DELIVERY"
        fuel_request = FuelRequest.objects.get(id=user.fuel_request.id)
        fuel_request.delivery_method = delivery_method
        fuel_request.save()
        user.position = 6 
        user.save()
        response_message = 'What is your payment method.\n\n1. ZWL(Cash)\n2. Ecocash\n3. RTGS(Swipe)/Transfer\n'
    elif user.position == 6:
        choice = payment_methods[int(message)]
        fuel_request = FuelRequest.objects.get(id=user.fuel_request.id)
        fuel_request.payment_method = choice
        fuel_request.save()
        response = recommend(fuel_request.fuel_type, fuel_request.amount, user.name.id, fuel_request.price)
        if response == False:
            pass
        else:
            offer = Offer.objects.filter(id=response).first()
            response_message = suggested_choice.format(offer.supplier.company.name, offer.request.fuel_type, offer.quantity, offer.price, offer.id)
        
        response_message = suggested_choice
    return response_message

def transacting_handler(user, message):
    if user.position == 1:
        if 'accept' in message.lower():
            offer_id = ''.join(x for x in message if x.isdigit())
            offer =  Offer.objects.filter(id=offer_id).first()
            if offer is not None:
                Transaction.objects.create(request_name=offer.request, buyer_name=user)
                response_message = 'This transaction has been completed'
        elif message.lower() == 'wait':
            pass
    return response_message




def fuel_finder():
    return 