from datetime import datetime, timedelta

from django.db.models import Sum

from supplier.models import Subsidiaries, Transaction, UserReview
# from company.models import Company, FuelUpdate
from buyer.models import User, FuelRequest
from national.models import Order
from company.models import CompanyFuelUpdate


def get_week_days(date):
    '''
    Get This Weeks Dates
    '''
    return [date + timedelta(days=i) for i in range(0 - date.weekday(), 7 - date.weekday())]

          
def get_weekly_sales(this_week, depot, currency):
    '''
    Get the company's weekly sales
    '''
    #Determine the week you wish to consider, this week or last week
    if this_week == True:
        date = datetime.now().date()
    else:
        date = datetime.now().date() - timedelta(days=7)    
    week_days = get_week_days(date)

    weekly_data = {}
    
    for day in week_days:
        weeks_revenue = Order.objects.filter(date=day, payment_approved=True,currency=currency, noic_depot=depot).aggregate(
            total = Sum('amount_paid')
        )['total'] 
        if weeks_revenue:
            weekly_data[day.strftime("%a")] = int(weeks_revenue)
        else:
            weekly_data[day.strftime("%a")] = 0.00    
    
    return weekly_data     


def get_aggregate_monthly_sales(year, depot, currency):
    '''
    Get the companies monthly sales
    '''

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_data = {}
    counter = 1

    for month in months:
        months_revenue = Order.objects.filter(date__year=year, currency=currency,date__month=counter, payment_approved=True, noic_depot=depot).aggregate(
            total = Sum('amount_paid')
        )['total']
        if months_revenue:
            monthly_data[month] = months_revenue
        else:
            monthly_data[month] = 0.0

        counter += 1    
                      
    return monthly_data    