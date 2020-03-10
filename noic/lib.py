import datetime

from national.models import NationalFuelUpdate, SordNationalAuditTrail, Order

def get_current_stock():
    stock = NationalFuelUpdate.objects.all().first()
    if stock:
        unallocated_diesel = stock.unallocated_diesel
        unallocated_petrol = stock.unallocated_petrol
    else:
        unallocated_diesel = 0.0
        unallocated_petrol = 0.0

    return unallocated_diesel, unallocated_petrol

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

def total_orders():
    return Order.objects.all().count()    


def get_monthly_orders():
    '''
    Get the companies monthly orders
    '''

    year = datetime.datetime.today().year

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_data = {}
    counter = 1
    for month in months:
        months_qty = 0
        months_orders = Order.objects.filter(date__year=year, date__month=counter)
        if months_orders:
            for order in months_orders :
                months_qty += order.quantity
        else:
            months_qty = 0

        counter += 1    
                     
        monthly_data[month] = months_qty
    return monthly_data    



