from supplier.models import Subsidiaries, Transaction, UserReview
from company.models import Company, FuelUpdate
from buyer.models import User
from datetime import datetime, timedelta



def top_branches(count,company):
    branches = Subsidiaries.objects.filter(is_depot=True).filter(company=company)
    subs = []

    for sub in branches:
        tran_amount = 0
        sub_trans = Transaction.objects.filter(supplier__company=company,supplier__subsidiary_id=sub.id, is_complete=True)
        for sub_tran in sub_trans:
            tran_amount += (sub_tran.offer.request.amount * sub_tran.offer.price)
        sub.tran_count = sub_trans.count()
        sub.tran_value = tran_amount
        subs.append(sub)

    # sort subsidiaries by transaction value
    sorted_subs = sorted(subs, key=lambda x: x.tran_value, reverse=True) 
    sorted_subs = sorted_subs[:count]
    return sorted_subs


def top_contributors(user):
    top_subs = top_branches(5,user.company)
    trans = get_total_revenue(user.company)


def get_week_days(date):
    return [date + timedelta(days=i) for i in range(0 - date.weekday(), 7 - date.weekday())]


def get_weekly_sales(company, this_week):
    if this_week == True:
        date = datetime.now().date()
    else:
        date = datetime.now().date() - timedelta(days=7)    
    week_days = get_week_days(date)
    weekly_data = {}
    for day in week_days:
        weeks_revenue = 0
        day_trans = Transaction.objects.filter(date=day, supplier__company=company, is_complete=True)
        if day_trans:
            for tran in day_trans:
                weeks_revenue += (tran.offer.request.amount * tran.offer.price)
        else:
            weeks_revenue = 0
        weekly_data[day.strftime("%a")] = int(weeks_revenue)
    return weekly_data               


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