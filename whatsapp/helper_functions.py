from django.shortcuts import render
import requests
from validate_email import validate_email
from .constants import *
from buyer.views import token_is_send
from supplier.models import Offer, Transaction, FuelAllocation, Subsidiaries
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
    if message.lower() == 'menu':
        user.stage = 'menu'
        user.position = 1
        user.fuel_updates_ids = " "
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
        fuel_request = FuelRequest.objects.get(id=user.fuel_request)
        if message == "1":
            fuel_request.delivery_method = "SELF COLLECTION"
            fuel_request.save()
            user.position = 6 
            user.save()
            response_message = 'What is your payment method.\n\n1. ZWL(Cash)\n2. Ecocash\n3. RTGS(Swipe)/Transfer\n4. USD'
            
        elif message == "2":
            fuel_request.delivery_method = "DELIVERY"
            fuel_request.save()
            response_message = "what is your location"
            user.position = 70 
            user.save()
        
        else:
            return "Incorrect Choice"   

    elif user.position == 70:
        fuel_request = FuelRequest.objects.get(id=user.fuel_request)
        fuel_request.delivery_address = message
        fuel_request.save()
        user.position = 6 
        user.save()
        response_message = 'What is your payment method.\n\n1. ZWL(Cash)\n2. Ecocash\n3. RTGS(Swipe)/Transfer\n4. USD'
          
    elif user.position == 6:
        try:
            choice = payment_methods[int(message)]
        except Exception as e:
            return "Wrong choice"
        fuel_request = FuelRequest.objects.get(id=user.fuel_request)
        fuel_request.payment_method = choice
        fuel_request.save()
        user.position = 7
        user.save()
        response_message = 'Please choose between the following:? \n\n1. Wait for Offers\n2. Get System Generated'

    elif user.position == 7:
        fuel_request = FuelRequest.objects.get(id=user.fuel_request)
        if message == "1":
            fuel_request.wait = True
            fuel_request.save()
            response_message = 'Request made successfully! Please wait for offers'
            
        elif message == "2":
            response = recommend(fuel_request)
            if response == False:
                response_message = 'Oops!!! Could not get best supplier for you, please type *1* to wait for offers'
            else:
                offer = Offer.objects.filter(id=response).first()
                response_message = suggested_choice.format(offer.supplier.company.name, offer.request.fuel_type, offer.quantity, offer.price, offer.id)
                user.position = 71
                user.save()
        
        else:
            return "Incorrect Choice"  

    elif user.position == 71:
        if 'accept' in message.lower():
            digits = [int(s) for s in message.split() if s.isdigit()]
            offer_id = int(digits[0])
            accepted_offer = Offer.objects.filter(id = offer_id).first()
            if accepted_offer is not None:
                offer = accepted_offer
                Transaction.objects.create(buyer=user,offer=offer,is_complete=True,supplier=offer.supplier)
                response_message = 'Transaction is complete'
            else:
                response_message = 'oops!! something went wrong during processing of your request, please type *Wait* to wait for offers'
                user.position = 72
                user.save()
        elif 'wait' in message.lower():
            fuel_request = FuelRequest.objects.get(id=user.fuel_request)
            fuel_request.wait = True
            fuel_request.save()
            response_message = 'Request made successfully! Please wait for offers'

        else:
            response_message = 'oops!! something went wrong during processing of your request, please type *Wait* to wait for offers or *Menu* to go back to main menu'
            user.position = 72
            user.save()



    return response_message


def follow_up(user, message):
    if user.position == 1:
        requests = FuelRequest.objects.filter(name=user).filter(wait=True).all()
        response_message = 'Which request do you want to follow? \n\n'
        i = 1
        for req in requests:
            response_message = response_message + str(i) + ". " + req.fuel_type + " " + str(req.amount) + "L" + " " + "made on" + " " + str(req.date) + '\n'
            i += 1        
        user.position = 21 
        user.save()
    elif user.position == 21:
        requests = FuelRequest.objects.filter(name=user).filter(wait=True).all()
        req = requests[int(message) - 1]
        offers = Offer.objects.filter(request=req).all()
        response_message = 'Which offer do you want to accept? \n\n'
        i = 1
        for offer in offers:
            response_message = response_message + str(i) + ". " + str(offer.quantity) + "L" + " " + "@" + " " + str(offer.price) + '\n'
            i += 1        
        user.position = 22
        user.fuel_request = req.id
        user.save()
    elif user.position == 22:
        req = FuelRequest.objects.filter(id = user.fuel_request).first()
        offers = Offer.objects.filter(request=req).all()
        offer = offers[int(message) - 1]
        Transaction.objects.create(buyer=user,offer=offer,is_complete=True,supplier=offer.supplier)
        response_message = 'Transaction is complete'
    return response_message


def view_fuel_updates(user, message):
    if user.position == 1:
        updates = FuelUpdate.objects.filter(~Q(sub_type='Company')).all()
        response_message = 'Which fuel update do you want? \n\n'
        i = 1
        for update in updates:
            sub = Subsidiaries.objects.filter(id = update.relationship_id).first()
            response_message = response_message + str(i) + ". " + sub.name + '\n' + "Petrol:" + " " + str(update.petrol_quantity) + " " + "Litres" + "\n" + "Price:" + " " + str(update.petrol_price) + "\n" + "Diesel:" + " " + str(update.diesel_quantity) + " " + "Litres" + "\n" + "Price:" + " " + str(update.diesel_price) + '\n\n'
            user.fuel_updates_ids = user.fuel_updates_ids + str(update.id) + " "
            user.save()
            i += 1        
        user.position = 31 
        user.save()
    elif user.position == 31:
        list1 = list(user.fuel_updates_ids.split(" "))
        update_id = list1[int(message)]
        update = FuelUpdate.objects.filter(id = update_id).first()
        my_request = FuelRequest.objects.create(name=user, is_direct_deal=True, last_deal=update_id)
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
        choice = payment_methods[int(message) - 1]
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
            my_request.save()
            response_message = 'made request successfully'
        elif message == "2":
            my_request.delivery_method = "DELIVERY"
            my_request.save()
            response_message = "what is your location"
            user.position = 36
            user.save()
        else:
            return "Incorrect Choice"        
        
    elif user.position == 36:
        my_request = FuelRequest.objects.get(id=user.fuel_request)
        my_request.delivery_address = message
        my_request.save()
        response_message = 'made request successfully'
    
   
    return response_message


def view_requests_handler(user, message):
    response_message = ""
    if user.position == 0:
        requests = FuelRequest.objects.filter(wait=True).all()
        response_message = 'Reply with the number of the request to make an offer? \n\n'
        i = 1
        for req in requests:
            fuel = str(req.fuel_type).capitalize()
            response_message = f'{response_message} *{i}.* {fuel} *{req.amount}* litres made on {req.date}\n'
            user.fuel_updates_ids = user.fuel_updates_ids + str(req.id) + " "
            user.save()
            i += 1        
        user.position = 1 
        user.save()
    elif user.position == 1:
        request_list = list(user.fuel_updates_ids.split(" "))
        try:
            request_id = request_list[int(message)]
            response_message = "How many litres are you offering?"
            fuel_request = FuelRequest.objects.filter(id=request_id).first()
            user.fuel_request = fuel_request.id
            user.position = 2
            user.save()
        except:
            response_message = "Incorrect choice! Please enter a valid choice"
            user.position = 1
            user.save()
    elif user.position == 2:
        fuel_request = FuelRequest.objects.filter(id=user.fuel_request).first()
        amount = fuel_request.amount
        try:
            offer_quantity = float(message)
            if offer_quantity <= amount:
                if Offer.objects.filter(request=fuel_request, supplier=user).exists():
                    offer = Offer.objects.filter(request=fuel_request, supplier=user).first()
                    offer.quantity = float(message)
                    offer.save()
                else:
                    Offer.objects.create(quantity=float(message), supplier=user, request=fuel_request)
                response_message = "At what price per litre?"
                user.position = 3
                user.save()
            else:
                response_message = "You can not offer fuel that is more than the requested quantity. Please enter a different fuel quantity."
                user.position = 2
                user.save()
        except:
            response_message = "Incorrect input! Please re-enter the number of litres you are offering"
            user.position = 2
            user.save()
    elif user.position == 3:
        fuel_request = FuelRequest.objects.filter(id=user.fuel_request).first()
        offer = Offer.objects.filter(supplier=user, request=fuel_request).first()
        try:
            offer.price = float(message)
            offer.save()
            response_message = "Offer successfully send! Type *menu* to go back"
            user.stage = "menu"
            user.position = 0
            user.save()
        except:
            response_message = "I expected a number or decimal not a string. Please enter a valid price"
            user.position = 3
            user.save()
    return response_message


def view_offers_handler(user, message):
    if user.position == 0:
        response_message = "Reply with the offer number to change the initial offer available\n\n"
        offers = Offer.objects.filter(supplier=user)
        i = 1
        for offer in offers:
            fuel = offer.request.fuel_type.capitalize()
            response_message = response_message + f'*{i}.* {fuel} *{offer.quantity}* litres at {offer.price} made on {offer.date}\n'
            user.fuel_updates_ids = user.fuel_updates_ids + str(offer.id) + " "
            user.save()
            i += 1
        user.position = 1
        user.save()
    elif user.position == 1:
        offer_list = list(user.fuel_updates_ids.split(" "))
        try:
            offer_id = offer_list[int(message)]
            response_message = "How many litres are you offering now?"
            offer = Offer.objects.filter(id=offer_id).first()
            user.position = 2
            user.fuel_request = offer.id
            user.save()
        except:
            response_message = "Invalid option! Please enter a valid option."
            user.position = 1
            user.save()
    elif user.position == 2:
        offer = Offer.objects.filter(id=user.fuel_request).first()
        request_quantity = offer.request.amount
        try:
            offer_quantity = float(message)
            if offer_quantity <= request_quantity:
                offer.quantity = float(message)
                offer.save()
                response_message = "At what price per litre?"
                user.position = 3
                user.save()
            else:
                response_message = "You can not offer fuel that is more than the requested quantity. Please enter a different fuel quantity."
                user.position = 2
                user.save()
        except:
            response_message = "Expected a number! Please re-enter a valid quantity."
            user.position = 2
            user.save()
    elif user.position ==3:
        offer = Offer.objects.filter(id=user.fuel_request).first()
        try:
            offer.price = float(message)
            offer.save()
            response_message = "You have successfully updated your offer"
            user.stage = "menu"
            user.position = 0
            user.save()
        except:
            response_message = "Expected a number! Please re-enter a valid price."
            user.position = 3
            user.save()
    return response_message


def view_transactions_handler(user, message):
    transactions = Transaction.objects.filter(supplier=user)
    if transactions:
        i = 1
        while i < 10:
            for transaction in transactions:
                response_message = f'{transaction.date} {transaction.time} {transaction.buyer.first_name} {transaction.buyer.last_name} {transaction.offer.quantity}'
                i += 1
    else:
        response_message = "You have not performed any transactions yet"
    return response_message


def supplier_handler(request,user,message):
    response_message = ""
    if message.lower() == 'menu':
        user.stage = 'menu'
        user.fuel_updates_ids = " "
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
        elif message == "2":
            user.stage = 'view_offers'
            user.position = 0
            user.save()
            response_message = view_offers_handler(user, message)
        elif message == "3":
            user.stage = 'menu'
            user.position = 0
            user.save()
            response_message = view_transactions_handler(user, message)
        else:
            response_message = "You entered an invalid option. Type *menu* to restart."
    elif user.stage == 'view_requests':
        response_message= view_requests_handler(user, message)
    elif user.stage == 'view_offers':
        response_message = view_offers_handler(user, message)
    else:
        pass

    return response_message

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



def service_station_handler(request,user,message):
    if message.lower() == 'menu':
        user.stage = 'menu'
        user.position = 1
        user.save()
        full_name = user.first_name + " " + user.last_name
        response_message = ss_supplier_menu.format(full_name)
        return response_message 
    if user.stage == 'menu':
        if message == "1":
            user.stage = 'update_petrol'
            user.save()
            response_message = update_petrol(user, message)
        elif message == "2":
            user.stage = 'update_diesel'
            user.save()
            response_message = update_diesel(user, message)
        elif message == "3":
            user.stage = 'view_allocations'
            user.save()
            response_message = view_allocations(user, message)
        else:
            full_name = user.first_name + " " + user.last_name
            response_message = ss_supplier_menu.format(full_name)
        return response_message   

    elif user.stage == 'update_petrol':
        response_message = update_petrol(user, message)
    elif user.stage == 'update_diesel':
        response_message = update_diesel(user, message)
    elif user.stage == 'view_allocations':
        response_message = view_allocations(user, message)
    elif user.stage == 'registration':
        user.stage = 'menu'
        user.position = 1        
        full_name = user.first_name + " " + user.last_name
        if user.activated_for_whatsapp: 
            response_message = ss_supplier_menu.format(full_name)           
        else:        
            response_message = registred_as_a.format(full_name, user.company.name, "SS_SUPPLIER")
        user.save()
    else:
       pass
    return response_message   


def update_petrol(user, message):
    if user.position == 1:
        update = FuelUpdate.objects.filter(sub_type='Service Station').filter(relationship_id=user.subsidiary_id).first()
        response_message = "The last update of Petrol quantity is" + " " + str(update.petrol_quantity) + "L" + "." + " " + "How many litres of petrol left?"
        user.position = 40
        user.save()
    elif user.position == 40:
        update = FuelUpdate.objects.filter(sub_type='Service Station').filter(relationship_id=user.subsidiary_id).first()
        update.petrol_quantity = message
        user.position = 41
        user.save()
        update.save()
        response_message = 'What is the queue size?\n\n1. Short\n2. Medium Long\n3. Long'
    elif user.position == 41:
        update = FuelUpdate.objects.filter(sub_type='Service Station').filter(relationship_id=user.subsidiary_id).first()
        if message == "1":
            update.queue_length = "Short"
        elif message == "2":
            update.queue_length = "Medium Long"
        elif message == "3":
            update.queue_length = "Long"
        else:
            response_message = 'wrong choice'
        update.save()
        user.position = 42
        user.save()
        response_message = "What is the status?\n\n1. Pumping\n2. Expecting More Fuel\n3. Empty\n4. Offloading"
    elif user.position == 42:
        update = FuelUpdate.objects.filter(sub_type='Service Station').filter(relationship_id=user.subsidiary_id).first()
        if message == "1":
            update.status = "Pumping"
            update.save()
            response_message = "made an update successfully"
        elif message == "2":
            update.status = "Expecting More Fuel"
            update.save()
            response_message = "made an update successfully"
        elif message == "3":
            update.status = "Empty"
            update.save()
            response_message = "made an update successfully"
        elif message == "4":
            update.status = "Offloading"
            update.save()
            response_message = "made an update successfully"
        else:
            response_message = 'wrong choice'
        
    return response_message

def update_diesel(user, message):
    if user.position == 1:
        update = FuelUpdate.objects.filter(sub_type='Service Station').filter(relationship_id=user.subsidiary_id).first()
        response_message = "The last update of Diesel quantity is" + " " + str(update.diesel_quantity) + "L" + "." + " " + "How many litres of diesel left?"
        user.position = 50
        user.save()
    elif user.position == 50:
        update = FuelUpdate.objects.filter(sub_type='Service Station').filter(relationship_id=user.subsidiary_id).first()
        update.diesel_quantity = message
        user.position = 51
        user.save()
        update.save()
        response_message = 'What is the queue size?\n\n1. Short\n2. Medium Long\n3. Long'
    elif user.position == 51:
        update = FuelUpdate.objects.filter(sub_type='Service Station').filter(relationship_id=user.subsidiary_id).first()
        response_message = "What is the status?\n\n1. Pumping\n2. Expecting More Fuel\n3. Empty\n4. Offloading"
        if message == "1":
            update.queue_length = "Short"
        elif message == "2":
            update.queue_length = "Medium Long"
        elif message == "3":
            update.queue_length = "Long"
        else:
            response_message = 'wrong choice'
        update.save()
        user.position = 52
        user.save()    
    elif user.position == 52:
        update = FuelUpdate.objects.filter(sub_type='Service Station').filter(relationship_id=user.subsidiary_id).first()
        if message == "1":
            update.status = "Pumping"
        elif message == "2":
            update.status = "Expecting More Fuel"
        elif message == "3":
            update.status = "Empty"
        elif message == "4":
            update.status = "Offloading"
        else:
            response_message = 'wrong choice'
        update.save()
        response_message = "made an update successfully"
    
    return response_message

def view_allocations(user, message):
    if user.position == 1:
        allocations = FuelAllocation.objects.filter(assigned_staff_id=user.subsidiary_id).all()
        response_message = 'The following are quantities of the fuel you received. Please type *menu* to go back to main menu. \n\n'
        i = 1
        for allocation in allocations:
            response_message = response_message + str(i) + "." + " " + str(allocation.date) + " " + "Diesel" + " " + str(allocation.diesel_quantity) + "L" + " " + "&" + " " + "Petrol" + " " +str(allocation.petrol_quantity) + "L" + '\n'
            i += 1        
        
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