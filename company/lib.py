from supplier.models import Subsidiaries, Transaction
from company.models import Company, FuelUpdate


def get_all_subsidiaries(company):
    return Subsidiaries.objects.filter(company=company)


def get_aggregate_stock(company):
    diesel = 0; petrol = 0
    for sub in get_all_subsidiaries(company):
        diesel += FuelUpdate.objects.filter(relationship_id=sub.id).first().diesel_quantity
        petrol += FuelUpdate.objects.filter(relationship_id=sub.id).first().petrol_quantity
    return {'diesel': diesel, 'petrol': petrol}


def get_total_revenue(company):
    revenue = 0
    user = company.user_set.get_queryset().first()
    for transaction in Transaction.objects.filter(supplier=user):
        revenue += transaction.request.amount
    return revenue