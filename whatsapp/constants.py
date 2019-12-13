individual_menu= '''
Hie, Lets help you find Fuel

Where are you?

1. Harare 
2. Bulawayo 
3. Mutare
4. Kariba 
5. Gweru 
6. Kwekwe 
7. Victoria Falls

'''

registred_as_a = '''
Hie {0}, This number has been registered with the below details

*Company Name*: {1}
*Role*: {2}

However for you to be able to use this platform you need to log in to your portal and click on the option *Activate Whatsapp* 

To use this platform as an individual buyer type *NO*
'''

buyer_menu='''
Hello {0}, What would you like to do today\n\n

1. Make a Fuel Request\n
2. Follow up on Fuel Request\n
3. View Fuel Updates

'''

individual_menu='''
Hello {0}, What would you like to do today\n

1. Look for Fuel\n
2. View Updates\n

'''

ss_supplier_menu='''
Hello {0}, What would you like to do today\n\n

1. Update Petrol Quantity\n
2. Update Diesel Quantity\n
3. View Today's Received Fuel

'''



supplier_menu = '''
Hello {0}, What would you like to do today\n

1. View Fuel Requests
2. View offers
3. Today's Received Fuel
4. Update Fuel Stocks
5. Mini Statement

'''
zimbabwean_towns = ["Beitbridge","Bindura","Bulawayo","Chinhoyi","Chirundu","Gweru","Harare","Hwange","Juliusdale","Kadoma","Kariba","Karoi","Kwekwe","Marondera", "Masvingo","Mutare","Mutoko","Nyanga","Victoria Falls"]


greetings_message = '''
*Hie {0}, Welcome To Intelli Fuel Finder* 

Intelli Fuel Finder is system that brings together individuals and corporates that are looking for fuel.
You can register on the plartform as a Supplier, Individual Buyer or Corporate Buyer.

To begin the registration process please select one of the below options 

*What would you like to register as*
1. Individual Buyer *_(200 litres and below)_* 
2. Corporate Buyer *_(1000 litres and above)_*
3. Bulk Supplier *_(Any amount)_*


Please Type the desired option to continue. 
'''

user_types=['individual', 'buyer', 'supplier']

successful_integration = '''
You have succesfully integrated your Whatsapp with you company account.

If you want to look for fuel, please type *Menu* 

'''

suggested_choice = '''
Please find the below available supplier for you 

*Company Name*: {0}
*Fuel Type*: {1}
*Quantity*: {2}
*Price*: {3}

To Accept this Offer Type *Accept {4}*

To Wait for offers type *Wait*

Type *Menu* to go back to Menu
'''

new_offer = '''
Please find the below offer for you

*Company Name*: {0}
*Fuel Type*: {1}
*Quantity*: {2}
*Price*: {3}

To Accept this Offer Type *Accept {4}*

To Wait for offers type *Wait*

To Close this request type *Close*

Type *Menu* to go back to Menu
'''

fuel_updates = '''
Which fuel update do you want

{}. *{}*: 
*Petrol*: {}
*Price*: {}
*Diesel*: {}
*Price*: {}

'''

payment_methods=['RTGS', 'ECOCASH', 'SWIPE', 'USD']