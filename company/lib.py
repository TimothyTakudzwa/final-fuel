from supplier.models import Subsidiaries, Transaction, UserReview
from company.models import Company, FuelUpdate
from buyer.models import User
from datetime import datetime


def get_monthly_sales(company, year):

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_data = {}
    counter = 1
    for month in months:
        months_revenue = 0
        months_trans = Transaction.objects.filter(date__year=year, date__month=counter, supplier__company=company)
        if months_trans:
            for tran in months_trans :
                months_revenue += (tran.offer.request.amount * tran.offer.price)
        else:
            months_revenue = 0

        counter += 1    
                     
        monthly_data[month] = months_revenue
    return monthly_data    

    

def get_average_rating(company):
    average_rating = 0
    reviews = UserReview.objects.filter(company_type='Supplier', company=company)
    
    for review in reviews:
        average_rating += review.rating

    try:
        average_rating = average_rating/reviews.count()
    except:
        average_rating = 0

    return average_rating            



def get_all_subsidiaries(company):
    return Subsidiaries.objects.filter(company=company)


def get_aggregate_stock(company): 
    fuel_update = FuelUpdate.objects.filter(sub_type="Company", company_id=company.id).first()
    if fuel_update:
        return {'diesel': fuel_update.diesel_quantity, 'petrol': fuel_update.petrol_quantity}
    return {'diesel': 0, 'petrol': 0}
    

def get_total_revenue(user):
    revenue = 0

    trans = Transaction.objects.filter(supplier__company=user.company, is_complete=True)
    
    if trans:
        for transaction in trans:
            revenue += (transaction.offer.request.amount * transaction.offer.price)
    else:
        revenue = 0        
    return revenue


def get_transactions_complete_percentage(user):
    try:
        trans = (Transaction.objects.filter(supplier__company=user.company, is_complete=True).count()/Transaction.objects.filter(supplier__company=user.company).count()) * 100
    except:
        trans = 0    
    return "{:,.1f}%".format(trans)


def get_aggregate_staff(company):
    return User.objects.filter(company=company)