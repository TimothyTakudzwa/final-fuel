from supplier.models import Subsidiaries, Transaction
from company.models import Company, FuelUpdate


def get_all_subsidiaries(company):
    return Subsidiaries.objects.filter(company=company)


def get_aggregate_stock(company):
    diesel = 0; petrol = 0
    for sub in get_all_subsidiaries(company):
        if FuelUpdate.objects.filter(relationship_id=sub.id).first():
            diesel += FuelUpdate.objects.filter(relationship_id=sub.id).first().diesel_quantity
            petrol += FuelUpdate.objects.filter(relationship_id=sub.id).first().petrol_quantity
        else:
            diesel = 0; petrol = 0    
    return {'diesel': diesel, 'petrol': petrol}


def get_total_revenue(user):
    revenue = 0
    for transaction in Transaction.objects.filter(supplier=user):
        revenue += transaction.offer.request.amount
    return revenue


def get_transactions_complete_percentage(user):
    trans = (Transaction.objects.filter(supplier=user, is_complete=True).count()/Transaction.objects.filter(supplier=user).count()) * 100
    return "{:,.1f}%".format(trans)


def get_aggregate_staff(company):
    return User.objects.filter(company=company, user_type='Supplier').filter(user_type='Service Station Rep')