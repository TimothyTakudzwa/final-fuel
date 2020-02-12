from datetime import datetime, timedelta

from supplier.models import Subsidiaries, Transaction, UserReview
# from company.models import Company, FuelUpdate
from buyer.models import User
from company.models import CompanyFuelUpdate


def get_top_branches(count,company):
    '''
    Get an ordered list of a companies top subsidiaries
    according to revenue generated
    '''
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


def get_top_contributors(user):
    '''
    Get the top 5 subsidiaries of a company
    '''
    top_subs = get_top_branches(5,user.company)
    trans = get_total_revenue(user.company)


def get_week_days(date):
    '''
    Get This Weeks Dates
    '''
    return [date + timedelta(days=i) for i in range(0 - date.weekday(), 7 - date.weekday())]


def get_weekly_sales(company, this_week):
    '''
    Get the company's weekly sales
    '''
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
    '''
    Get the companies monthly sales
    '''

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
    '''
    Get company's average rating from user reviews
    '''
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
    '''
    Get all company subsidiaries
    '''
    return Subsidiaries.objects.filter(company=company)


def get_aggregate_stock(company):
    '''
    Get a company's total inventory
    ''' 
    fuel_update = CompanyFuelUpdate.objects.filter(company=company.id).first()
    if fuel_update:
        allocated_diesel = fuel_update.allocated_diesel
        unallocated_diesel = fuel_update.unallocated_diesel
        allocated_petrol = fuel_update.allocated_petrol
        unallocated_petrol = fuel_update.unallocated_petrol
        return {'diesel': (allocated_diesel + unallocated_diesel), 'petrol': (allocated_petrol + unallocated_petrol), 'allocated_diesel': allocated_diesel, 'unallocated_diesel': unallocated_diesel,
        'allocated_petrol': allocated_petrol, 'unallocated_petrol':unallocated_petrol }
    return {'diesel': 0, 'petrol': 0, 'allocated_diesel':0, 'unallocated_diesel': 0, 'allocated_petrol': 0, 'unallocated_petrol':0}
    

def get_total_revenue(user):
    '''
    Get a company's total sales revenue
    '''
    revenue = 0

    trans = Transaction.objects.filter(supplier__company=user.company, is_complete=True)
    
    if trans:
        for transaction in trans:
            revenue += (transaction.offer.request.amount * transaction.offer.price)
    else:
        revenue = 0        
    return revenue


def get_transactions_complete_percentage(user):
    '''
    Get % of complete transactions
    '''
    try:
        trans = (Transaction.objects.filter(supplier__company=user.company, is_complete=True).count()/Transaction.objects.filter(supplier__company=user.company).count()) * 100
    except:
        trans = 0    
    return "{:,.1f}%".format(trans)


def get_aggregate_staff(company):
    '''
    Get list of all the staff belonging to a company
    '''
    return User.objects.filter(company=company)