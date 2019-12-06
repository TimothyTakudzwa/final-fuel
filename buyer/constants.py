from company.models import Company
COMPANY_CHOICES = ''
try:
    companies = Company.objects.all()
    for company in companies: 
        COMPANY_CHOICES = tuple([(company.id, company.name) for company in companies])
except:
    pass
        
recommender_response = ''' 
Based on the Supplied details we have found the below fuel provider 

Company Name: {0}
Depot: {1}
Fuel Type: {2}
Quantity: {3}Litres
Price: {4}

'''

DELIVERY_OPTIONS= (('BULK', 'BULK'),('REGULAR', 'REGULAR'))

FUEL_CHOICES = (('Petrol', 'Petrol'),('DIESEL', 'Diesel'))

sender = f'Fuel Finder Accounts<tests@marlvinzw.me>'
subject = 'User Registration'

PAYING_CHOICES = (('USD', 'USD'),('TRANSFER','TRANSFER'),('BOND CASH','BOND CASH'),('USD & TRANSFER','USD & TRANSFER'),('TRANSFER & BOND CASH','TRANSFER & BOND CASH'),('USD & BOND CASH','USD & BOND CASH'),('USD, TRANSFER & BOND CASH','USD, TRANSFER & BOND CASH'))

STORAGE_TANKS = (('ABOVE GROUND', 'ABOVE GROUND'), ('BELOW GROUND','BELOW GROUND'))


sample_data = [
    {
        'company_id' : 1,
        'company_name': 'Total Zimbabwe',
        'fuel_type' : 'Petrol',
        'price' : '$0.75', 
        'quantity' : '5000l', 
        'updated_on' : 'September 13 2019', 
    },
      {
        'company_id' : 2,
        'company_name': 'Zuva Zimbabwe',
        'fuel_type' : 'Diesel',
        'price' : '$1.25', 
        'quantity' : '200 000L', 
        'updated_on' : 'June 5 2017', 
    },
      {
        'company_id' : 3,
        'company_name': 'Trek Zimbabwe',
        'fuel_type' : 'Petrol',
        'price' : '$1.12', 
        'quantity' : '500L', 
        'updated_on' : 'July 7 2019', 
    },
]