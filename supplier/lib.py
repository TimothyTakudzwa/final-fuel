from datetime import datetime, date, timedelta

from buyer.models import *
from supplier.models import *
import decimal

def get_customer_contributions(supplier_id, buyer_company):
    supplier = User.objects.filter(id=supplier_id).first()
    # buyer = User.objects.filter(id=buyer_id)
    total_transactions = Transaction.objects.filter(supplier=supplier)
    transactions_with_buyer = Transaction.objects.filter(supplier=supplier, buyer__company=buyer_company)
    try:
        percentage = (float(transactions_with_buyer.count()/total_transactions.count())) * 100
    except:
        percentage = 0    
    percentage = str(percentage) + "%"
    cash_total_transactions = Transaction.objects.filter(supplier=supplier, is_complete=True)
    cash_transactions_with_buyer = Transaction.objects.filter(supplier=supplier, buyer__company=buyer_company, is_complete=True)
    try:
        cash_percentage = cash_transactions_with_buyer.count()/cash_total_transactions.count()
    except:
        cash_percentage = 0
    cash_percentage = str(cash_percentage) + "%"
    return percentage, cash_percentage


def client_revenue(supplier_id,buyer_company):
    supplier = User.objects.filter(id=supplier_id).first()
    cash_trans = 0
    for trans in Transaction.objects.filter(supplier=supplier, buyer__company=buyer_company, is_complete=True):
        cash_trans += (trans.offer.request.amount * trans.offer.price)
    return cash_trans

def total_requests(buyer_company):
    yesterday = date.today() - timedelta(days=1)
    all_reqs = FuelRequest.objects.filter(name__company=buyer_company).count()  
    today_reqs = FuelRequest.objects.filter(name__company=buyer_company,date__gt=yesterday).count() 
    return all_reqs, today_reqs

def transactions_total_cost(buyer):
    revenue = 0
    trans = Transaction.objects.filter(buyer=buyer, is_complete=True).all()
    if trans:
        for tran in trans:
            revenue += (decimal.Decimal(tran.offer.request.amount) * tran.offer.price)
    return revenue 

def total_offers(buyer):
    yesterday = date.today() - timedelta(days=1)
    all_offers = Offer.objects.filter(request__name=buyer).count()
    todays_offers = Offer.objects.filter(request__name=buyer, date__gt=yesterday).count()
    return all_offers, todays_offers




