from datetime import datetime, timedelta

from supplier.models import Subsidiaries, Transaction, UserReview
# from company.models import Company, FuelUpdate
from buyer.models import User
from company.models import CompanyFuelUpdate


def get_top_branches(count):
    '''
    Get an ordered list of a companies top subsidiaries
    according to revenue generated
    '''
    branches = Subsidiaries.objects.all()
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
    top_subs = get_top_branches(5)
    trans = get_aggregate_total_revenue()


def get_week_days(date):
    '''
    Get This Weeks Dates
    '''
    return [date + timedelta(days=i) for i in range(0 - date.weekday(), 7 - date.weekday())]


def get_weekly_sales(this_week):
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
        day_trans = Transaction.objects.filter(date=day, is_complete=True)
        if day_trans:
            for tran in day_trans:
                weeks_revenue += (tran.offer.request.amount * tran.offer.price)
        else:
            weeks_revenue = 0
        weekly_data[day.strftime("%a")] = int(weeks_revenue)
    return weekly_data               


def get_aggregate_monthly_sales(year):
    '''
    Get the companies monthly sales
    '''

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_data = {}
    counter = 1
    for month in months:
        months_revenue = 0
        months_trans = Transaction.objects.filter(date__year=year, date__month=counter)
        if months_trans:
            for tran in months_trans :
                months_revenue += (tran.offer.request.amount * tran.offer.price)
        else:
            months_revenue = 0

        counter += 1    
                     
        monthly_data[month] = months_revenue
    return monthly_data    

    
def get_all_subsidiaries(company):
    '''
    Get all company subsidiaries
    '''
    return Subsidiaries.objects.filter(company=company)


def get_aggregate_stock():
    '''
    Get a company's total inventory
    ''' 
    fuel_updates = CompanyFuelUpdate.objects.all()
    
    if fuel_updates:
        for update in fuel_updates:
            allocated_diesel += update.allocated_diesel
            unallocated_diesel += update.unallocated_diesel
            allocated_petrol += update.allocated_petrol
            unallocated_petrol += update.unallocated_petrol
        return {'diesel': (allocated_diesel + unallocated_diesel), 'petrol': (allocated_petrol + unallocated_petrol), 'allocated_diesel': allocated_diesel, 'unallocated_diesel': unallocated_diesel,
        'allocated_petrol': allocated_petrol, 'unallocated_petrol':unallocated_petrol }
    return {'diesel': 0, 'petrol': 0, 'allocated_diesel':0, 'unallocated_diesel': 0, 'allocated_petrol': 0, 'unallocated_petrol':0}
    

def get_aggregate_total_revenue():
    '''
    Get a company's total sales revenue
    '''
    revenue = 0

    trans = Transaction.objects.filter(is_complete=True)
    
    if trans:
        for transaction in trans:
            revenue += (transaction.offer.request.amount * transaction.offer.price)
    else:
        revenue = 0        
    return revenue


def get_aggregate_transactions_complete_percentage():
    '''
    Get % of complete transactions
    '''
    try:
        trans = (Transaction.objects.filter(is_complete=True).count()/Transaction.objects.all().count()) * 100
    except:
        trans = 0    
    return "{:,.1f}%".format(trans)
