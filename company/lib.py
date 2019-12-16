from supplier.models import Subsidiaries, Transaction
from company.models import Company, FuelUpdate
from buyer.models import User


def get_all_subsidiaries(company):
    return Subsidiaries.objects.filter(company=company)


def get_aggregate_stock(company): 
    fuel_update = FuelUpdate.objects.filter(sub_type="Company", company_id = company.id).first()
    if fuel_update:
        return {'diesel': fuel_update.diesel_quantity, 'petrol': fuel_update.petrol_quantity}
    return {'diesel': 0, 'petrol': 0}
    

def get_total_revenue(user):
    revenue = 0

    for transaction in Transaction.objects.filter(supplier__company=user.company, is_complete=True):
        revenue += transaction.offer.request.amount
    return revenue


def get_transactions_complete_percentage(user):
    try:
        trans = (Transaction.objects.filter(supplier__company=user.company, is_complete=True).count()/Transaction.objects.filter(supplier__company=user.company).count()) * 100
    except:
        trans = 0    
    return "{:,.1f}%".format(trans)


def get_aggregate_staff(company):
    return User.objects.filter(company=company)