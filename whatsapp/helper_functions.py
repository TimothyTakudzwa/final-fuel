from django.shortcuts import render
import requests
from validate_email import validate_email
from .constants import *
from buyer.views import token_is_send
from supplier.models import Offer, Transaction
from buyer.models import User, FuelRequest
from company.models import FuelUpdate
from django.db.models import Q
from buyer.recommend import recommend


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
    if message == 'menu':
        user.stage = 'menu'
        user.position = 1
        user.save()
        full_name = user.first_name + " " + user.last_name
        response_message = buyer_menu.format(full_name)
        return response_message 
    if user.stage == 'menu':
        if message == "1":
            user.stage = 'make_fuel_request'
            user.save()
            response_message = requests_handler(user, message)
        elif message == "2":
            user.stage = 'follow_up'
            user.save()
            response_message = follow_up(user, message)
        elif message == "3":
            user.stage = 'fuel_update'
            user.save()
            response_message = view_fuel_updates(user, message)
        else:
            full_name = user.first_name + " " + user.last_name
            response_message = buyer_menu.format(full_name)
        return response_message   
    elif user.stage == 'make_fuel_request':
        response_message = requests_handler(user, message)
    elif user.stage == 'follow_up':
        response_message = follow_up(user, message)
    elif user.stage == 'fuel_update':
        response_message = view_fuel_updates(user, message)
    elif user.stage == 'registration':
        user.stage = 'menu'
        user.position = 1        
        full_name = user.first_name + " " + user.last_name
        if user.activated_for_whatsapp: 
            response_message = buyer_menu.format(full_name)           
        else:        
            response_message = registred_as_a.format(full_name, user.company.name, "Buyer")
        user.save()
    else:
       pass
    return response_message   

def requests_handler(user, message):    
    if user.position == 1:
        response_message = "Which type of fuel do you want\n\n1. Petrol\n2. Diesel"
        user.position = 3
        user.save()
    elif user.position == 3:
        response_message = "How many litres do you want?"
        if message == "1":
            fuel_type = "Petrol"
        elif message == "2":
            fuel_type = "Diesel"
        else:
            return "Incorrect Choice"
        fuel_request = FuelRequest.objects.create(fuel_type=fuel_type, name=user)
        user.fuel_request = fuel_request.id
        user.position = 4
        user.save()
    elif user.position == 4:
        fuel_request = FuelRequest.objects.get(id=user.fuel_request)
        fuel_request.amount = message
        fuel_request.save()
        user.position = 5
        user.save()
        response_message = "*Please select delivery method*\n\n1. Pick Up\n2. Delivery"       
    elif user.position == 5: 
        if message == "1":
            delivery_method = "SELF COLLECTION"
        elif message == "2":
            delivery_method = "DELIVERY"
        else:
            return "Incorrect Choice"        
        fuel_request = FuelRequest.objects.get(id=user.fuel_request)
        fuel_request.delivery_method = delivery_method
        fuel_request.save()
        user.position = 6 
        user.save()
        response_message = 'What is your payment method.\n\n1. ZWL(Cash)\n2. Ecocash\n3. RTGS(Swipe)/Transfer\n4. USD'
    elif user.position == 6:
        choice = payment_methods[int(message)]
        fuel_request = FuelRequest.objects.get(id=user.fuel_request)
        fuel_request.payment_method = choice
        fuel_request.save()
        response = recommend(fuel_request)
        if response == False:
            pass
        else:
            offer = Offer.objects.filter(id=response).first()
            response_message = suggested_choice.format(offer.supplier.company.name, offer.request.fuel_type, offer.quantity, offer.price, offer.id)
        
        response_message = suggested_choice
    return response_message


def follow_up(user, message):
    if user.position == 1:
        response_message = "1. Proceed \n 2. Cancel"
        user.position = 20
        user.save()
    elif user.position == 20:
        requests = FuelRequest.objects.filter(name=user).filter(wait=True).all()
        response_message = 'Which request do you want to follow? \n\n'
        i = 1
        for req in requests:
            response_message = response_message + str(req.id) + ". " + req.fuel_type + str(req.amount) + '\n'
            i += 1        
        user.position = 21 
        user.save()
    elif user.position == 21:
        req = FuelRequest.objects.filter(id = int(message)).first()
        offers = Offer.objects.filter(request=req).all()
        response_message = 'Which offer do you want to accept? \n\n'
        i = 1
        for offer in offers:
            response_message = response_message + str(offer.id) + ". " + str(offer.quantity) + "@" + str(offer.price) + '\n'
            i += 1        
        user.position = 22
        user.fuel_request = req.id
        user.save()
    elif user.position == 22:
        req = FuelRequest.objects.filter(id = user.fuel_request).first()
        offer = Offer.objects.filter(id=int(message)).first()
        Transaction.objects.create(buyer=user,offer=offer,is_complete=True)
        response_message = 'Transaction is complete'
    return response_message


def view_fuel_updates(user, message):
    if user.position == 1:
        response_message = "1. Proceed \n2. Cancel"
        user.position = 30
        user.save()
    elif user.position == 30:
        updates = FuelUpdate.objects.filter(~Q(sub_type='Company')).all()
        response_message = 'Which fuel update do you want? \n\n'
        i = 1
        for update in updates:
            response_message = response_message + str(update.id) + ". " + "Petrol" + str(update.petrol_quantity) + "@" + str(update.petrol_price) + "and" + "Diesel" + str(update.diesel_quantity) + "@" + str(update.diesel_price) + '\n'
            i += 1        
        user.position = 31 
        user.save()
    elif user.position == 31:
        #update = FuelUpdate.objects.filter(id = int(message)).first()
        my_request = FuelRequest.objects.create(name=user, is_direct_deal=True)
        user.fuel_request = my_request.id
        response_message = "Which type of fuel do you want\n\n1. Petrol\n2. Diesel"
        user.position = 32
        user.save()
    elif user.position == 32:
        my_request = FuelRequest.objects.get(id=user.fuel_request)
        if message == "1":
            my_request.fuel_type = "Petrol"
        elif message == "2":
            my_request.fuel_type = "Diesel"
        else:
            return "Incorrect Choice"
        my_request.save()
        user.position = 33
        user.save()
        response_message = "How many litres do you want?"
    elif user.position == 33:
        my_request = FuelRequest.objects.get(id=user.fuel_request)
        my_request.amount = message
        my_request.save()
        user.position = 34
        user.save()
        response_message = 'What is your payment method.\n\n1. ZWL(Cash)\n2. Ecocash\n3. RTGS(Swipe)/Transfer\n4. USD'
    elif user.position == 34:
        choice = payment_methods[int(message)]
        my_request = FuelRequest.objects.get(id=user.fuel_request)
        my_request.payment_method = choice
        my_request.save()
        user.position = 35
        user.save()
        response_message = "*Please select delivery method*\n\n1. Pick Up\n2. Delivery"
    elif user.position == 35:
        my_request = FuelRequest.objects.get(id=user.fuel_request)
        if message == "1":
            my_request.delivery_method = "SELF COLLECTION"
        elif message == "2":
            my_request.delivery_method = "DELIVERY"
        else:
            return "Incorrect Choice"        
        my_request.save()
   
    return response_message


def view_requests_handler(user, message):
    response_message = ""
    if user.position == 0:
        requests = FuelRequest.objects.filter(wait=True).all()
        response_message = 'Which request do you want to make an offer? \n\n'
        i = 1
        for req in requests:
            response_message = response_message + str(req.id) + ". " + req.fuel_type + str(req.amount) + '\n'
            i += 1        
        user.position = 1 
        user.save()
    elif user.position == 1:
        fuel_request = FuelRequest.objects.filter(id=int(message)).first()
        user.fuel_request = fuel_request
        response_message = "How many litres are you offering?"
        user.position = 2
        user.save()
    elif user.position == 2:
        Offer.objects.create(quantity=float(message), supplier=request.user, request=fuel_request)
        response_message = "At what price per litre?"
        user.position = 3
        user.save()
    elif user.position == 3:
        offer = Offer.objects.filter(supplier=request.user, request=fuel_request).first()
        offer.price = float(message)
        offer.save()
        response_message = "Offer successfully send! Press *menu* to go back"
    return response_message


def supplier_handler(request,user,message):
    response_message = ""
    if message.lower() == 'menu':
        user.stage = 'menu'
        user.position = 1
        user.save()
        full_name = user.first_name + " " + user.last_name
        response_message = supplier_menu.format(full_name)
        return response_message
    elif user.stage == 'menu':
        if message == "1":
            user.stage = 'view_requests'
            user.position = 0
            user.save()
            response_message = view_requests_handler(user, message)
        # elif message == "2":
        #     user.stage = 'view_offers'
        #     user.position = 0
        #     user.save()
        #     response_message = view_offers_handler(user, message)

    return response_message

def service_station_handler(request,user,message):
    if message.lower() == 'menu' and user.stage != 'registration':
        user.position = 1
        user.stage = 'requesting'
        user.save()
        return requests_handler(user, message)
    pass


def bot_action(request, user, message):   
    if user.stage == 'registration' and user.position !=0:
        return registration_handler(request, user, message)
    if user.user_type == 'INDIVIDUAL':
        return individual_handler(request, user, message)
        
    elif user.user_type == 'S_ADMIN':
        return "You are not allowed to use this platform"
    elif user.user_type == 'BUYER':
        return buyer_handler(request, user,message)
    elif user.user_type == 'SUPPLIER':
        return supplier_handler(request, user, message)
    elif user.user_type == 'SS_SUPPLIER':
        return service_station_handler(request, user,message)    
    


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