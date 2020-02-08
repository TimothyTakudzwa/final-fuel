from datetime import datetime, date, timedelta

from buyer.models import *
from supplier.models import *

def get_customer_contributions(supplier_id, buyer_company):
    supplier = User.objects.filter(id=supplier_id).first()
    # buyer = User.objects.filter(id=buyer_id)
    total_transactions = Transaction.objects.filter(supplier=supplier)
    transactions_with_buyer = Transaction.objects.filter(supplier=supplier, buyer__company=buyer_company)
    percentage = (float(transactions_with_buyer.count()/total_transactions.count())) * 100
    percentage = str(percentage) + "%"
    cash_total_transactions = Transaction.objects.filter(supplier=supplier, is_complete=True)
    cash_transactions_with_buyer = Transaction.objects.filter(supplier=supplier, buyer__company=buyer_company, is_complete=True)
    cash_percentage = cash_transactions_with_buyer.count()/cash_total_transactions.count()
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



