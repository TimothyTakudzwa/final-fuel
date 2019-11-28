from buyer.models import Company
COMPANY_CHOICES = ''
try:
    companies = Company.objects.all()
    for company in companies: 
        COMPANY_CHOICES = tuple([(company.id, company.name) for company in companies])
except:
    pass
        

# COMPANY_CHOICES = (('ZB FINANCIAL HOLDINGS', 'ZB Financial Holdings'),('CBZ FINANCIAL HOLDINGS', 'CBZ Financial Holdings'),('DOVES HOLDINGS ZIMBABWE', 'Doves Holdings Zimbabwe'))
sender = f'Fuel Finder Accounts<tests@marlvinzw.me>'
subject = 'User Registration'

PAYING_CHOICES = (('USD', 'USD'),('TRANSFER','TRANSFER'),('BOND CASH','BOND CASH'),('USD & TRANSFER','USD & TRANSFER'),('TRANSFER & BOND CASH','TRANSFER & BOND CASH'),('USD & BOND CASH','USD & BOND CASH'),('USD, TRANSFER & BOND CASH','USD, TRANSFER & BOND CASH'))

sample_data = [
    {
        'company_id' : 1,
        'company_name': 'Intelli Africa Solutions',
        'fuel_type' : 'Petrol',
        'price' : '$1.25', 
        'quantity' : '$1.25', 
        'updated_on' : '$1.25', 
    },
      {
        'company_id' : 1,
        'company_name': 'Intelli Africa Solutions',
        'fuel_type' : 'Petrol',
        'price' : '$1.25', 
        'quantity' : '$1.25', 
        'updated_on' : '$1.25', 
    },
      {
        'company_id' : 1,
        'company_name': 'Intelli Africa Solutions',
        'fuel_type' : 'Petrol',
        'price' : '$1.25', 
        'quantity' : '$1.25', 
        'updated_on' : '$1.25', 
    },
]