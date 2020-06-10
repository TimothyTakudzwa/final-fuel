import datetime

from django.db.models import Sum, Count

from national.models import NationalFuelUpdate, SordNationalAuditTrail, Order

def get_current_usd_stock():
    inventory_usd = type('test', (object,), {})()
    stock_usd = NationalFuelUpdate.objects.filter(currency='USD').first()
    
    if stock_usd:
        inventory_usd.diesel_quantity = stock_usd.unallocated_diesel
        inventory_usd.petrol_quantity  = stock_usd.unallocated_petrol
    else:
        inventory_usd.diesel_quantity = 0.0
        inventory_usd.petrol_quantity  = 0.0

    return inventory_usd

def get_current_zwl_stock():
    inventory_zwl = type('test', (object,), {})()
    stock_zwl = NationalFuelUpdate.objects.filter(currency='RTGS').first()
    if stock_zwl:
        inventory_zwl.diesel_quantity = stock_zwl.unallocated_diesel
        inventory_zwl.petrol_quantity  = stock_zwl.unallocated_petrol
    else:
        inventory_zwl.diesel_quantity = 0.0
        inventory_zwl.petrol_quantity  = 0.0
    return inventory_zwl    




def get_total_allocations():

    total_allocations = 0

    for allocation_quantity in SordNationalAuditTrail.objects.all():
        total_allocations += allocation_quantity.quantity

    return total_allocations


def get_complete_orders_percentage():
    '''
    Get % of complete orders
    '''
    try:
        orders_complete_percentage = (Order.objects.filter(payment_approved=True).count()/Order.objects.all().count()) * 100
    except:
        orders_complete_percentage = 0    
    return "{:,.1f}%".format(orders_complete_percentage)


def orders_made_this_week():
    number_of_orders_this_week = Order.objects.filter(date__lte=datetime.datetime.today(), date__gt=datetime.datetime.today()-datetime.timedelta(days=7)).count()
    return number_of_orders_this_week


def get_week_days(date):
    '''
    Get This Weeks Dates
    '''
    return [date + datetime.timedelta(days=i) for i in range(0 - date.weekday(), 7 - date.weekday())]

            
def get_weekly_orders(this_week, currency):
    '''
    Get the company's weekly sales
    '''
    if this_week == True:
        date = datetime.datetime.now().date()
    else:
        date = datetime.datetime.now().date() - datetime.timedelta(days=7)    
    week_days = get_week_days(date)

    weekly_data = {}

    for day in week_days:
        weeks_revenue = 0
        day_trans = Order.objects.filter(date=day, payment_approved=True,
         currency=currency)
        if day_trans:
            weeks_revenue = day_trans.filter(date=day, payment_approved=True).aggregate(
                total=Sum('amount_paid')
            )['total']
        else:
            weeks_revenue = 0
        weekly_data[day.strftime("%a")] = int(weeks_revenue)
    return weekly_data 



def total_orders():
    return Order.objects.all().count()    


def get_monthly_orders(currency, year):
    '''
    Get the companies monthly orders
    '''

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_data = {}
    counter = 1
    for month in months:
        months_qty = Order.objects.filter(date__year=year, date__month=counter, currency=currency).aggregate(
            total=Sum('amount_paid')
        )['total']
        # months_orders = Order.objects.filter(date__year=year, date__month=counter)
        # if months_orders:
        #     for order in months_orders :
        #         months_qty += order.amount_paid
        # else:
        #     months_qty = 0

        counter += 1    
        
        if months_qty:             
            monthly_data[month] = months_qty
        else:
            monthly_data[month] = 0.00

    return monthly_data    


def get_top_clients(currency):
    fuel_orders = Order.objects.filter(payment_approved=True,currency=currency).annotate(
        number_of_orders=Count('noic_depot')).order_by('-number_of_orders')
    all_clients = [order.noic_depot for order in fuel_orders]

    new_clients = []
    for client in all_clients:
        new_client_orders = Order.objects.filter(noic_depot=client, payment_approved=True).all()
        total_client_orders = []
        client.total_revenue = new_client_orders.aggregate(total=Sum('amount_paid'))['total']
        client.total_client_orders = new_client_orders.count()
        if client not in new_clients and client.total_revenue:
            new_clients.append(client)
    clients = sorted(new_clients, key=lambda x: x.total_revenue, reverse=True)
    return clients        



