from datetime import datetime, timedelta

from supplier.models import Subsidiaries, Transaction, UserReview
# from company.models import Company, FuelUpdate
from buyer.models import User, FuelRequest
from company.models import CompanyFuelUpdate

from .constants import zimbabwean_towns, major_cities

import pandas
from django.db.models import Sum, Count

        
def get_top_branches(count):
    '''
    Get an ordered list of a companies top subsidiaries
    according to revenue generated
    '''

    branches = Subsidiaries.objects.filter(is_depot=True)
    # Retrieve all Subsidiaries

    subs = []

    for sub in branches:
        # Fetch all transactions related to Subsidiaries
        sub_trans = Transaction.objects.filter(supplier__subsidiary_id=sub.id, is_complete=True)
        # Get number of transaction objects
        sub.tran_count = sub_trans.count()
        # Get all the expected incomes from transactions qs 
        sub.tran_value = sub_trans.aggregate(total=Sum('expected'))['total']
        # Filter out null values
        if sub.tran_value:
            subs.append(sub)    

    # Sort subsidiaries by transaction value
    sorted_subs = sorted(subs, key=lambda x: x.tran_value, reverse=True) 
    # Slice subs list according to cutoff value. N items
    sorted_subs = sorted_subs[:count]
    return sorted_subs


def get_top_clients(count):
    # Sort all transactions in order of the number of times a buyer appears. 
    trans = Transaction.objects.filter(is_complete=True).annotate(
        number_of_trans=Count('buyer')).order_by('-number_of_trans')[:count]
    
    # Add all the buyers in a list to the variable buyers from the QS above
    buyers = [client.buyer for client in trans]

    # Var which will be used to represent the buyers immediately after processing
    new_buyers = []

    # Loop that will add attach all transaction data to our client objects
    for buyer in buyers:
        # accumulate all the transactions associated with the buyer
        new_buyer_transactions = trans.filter(buyer=buyer, is_complete=True).all()    
        buyer.total_revenue = new_buyer_transactions.aggregate(total=Sum('expected'))['total']
        buyer.purchases = new_buyer_transactions
        buyer.number_of_trans = new_buyer_transactions.count()
        if buyer not in new_buyers and buyer.total_revenue:
            new_buyers.append(buyer)

    clients = sorted(new_buyers, key=lambda x: x.total_revenue, reverse=True)


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


# def get_weekly_sales(this_week):
#     '''
#     Get the company's weekly sales
#     '''
#     if this_week == True:
#         date = datetime.now().date()
#     else:
#         date = datetime.now().date() - timedelta(days=7)    
#     week_days = get_week_days(date)
#     weekly_data = {}
#     for day in week_days:
#         weeks_revenue = 0
#         day_trans = Transaction.objects.filter(date=day, is_complete=True)
#         if day_trans:
#             for tran in day_trans:
#                 weeks_revenue += tran.expected
#         else:
#             weeks_revenue = 0
#         weekly_data[day.strftime("%a")] = int(weeks_revenue)
#     return weekly_data      

def get_weekly_sales(this_week):
    '''
    Get the company's weekly sales
    '''
    if this_week == True:
        date = datetime.now().date()
    else:
        date = datetime.now().date() - timedelta(days=7)    
    week_days = get_week_days(date)

    start_date = week_days[0]
    end_date = week_days[-1]

    weekly_transactions = Transaction.objects.filter(date__range=[start_date,end_date], is_complete=True)

    weekly_data = {}
    for day in week_days:
        if weekly_transactions:
            for tran in weekly_transactions:
                weeks_revenue = weekly_transactions.filter(date=day).aggregate(total=Sum('expected'))['total']
                if weeks_revenue:
                    weekly_data[day.strftime("%a")] = int(weeks_revenue)
                else:
                    weekly_data[day.strftime("%a")] = 0
        else:
            weekly_data = {'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0}

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
                # months_revenue += (float(tran.offer.request.amount) * float(tran.offer.price))
                months_revenue += tran.expected

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
        allocated_diesel=0
        unallocated_diesel=0
        allocated_petrol=0
        unallocated_petrol=0
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
            revenue += (float(transaction.offer.request.amount) * float(transaction.offer.price))
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


def get_approved_company_complete_percentage():
    '''
    Get % of complete transactions
    '''
    try:
        company_approval_percentage = (Company.objects.filter(is_verified=True).count()/Company.objects.all().count()) * 100
    except:
        company_approval_percentage = 0    
    return "{:,.1f}%".format(company_approval_percentage)


def get_subsidiary_sales_volume_in_city(user,city):
    volume = 0
    subs = Subsidiaries.objects.filter(id=user.subsidiary_id, city=city)
    if subs:
        for sub in subs:
            sub_trans = Transaction.objects.filter(supplier__company=user.company, supplier__subsidiary_id=sub.id,
                                                is_complete=True)
            for sub_tran in sub_trans:
                volume += sub_tran.offer.quantity
    return volume

def get_subsidiary_requests_volume_in_city(user,city):
    volume = 0
    subs = Subsidiaries.objects.filter(id=user.subsidiary_id, city=city)
    if subs:
        for sub in subs:
            sub_trans = Transaction.objects.filter(supplier__company=user.company, supplier__subsidiary_id=sub.id,
                                                is_complete=True)
            for sub_tran in sub_trans:
                volume += sub_tran.offer.request.amount
    return volume


def get_subsidiary_sales_volume_in_location(user, location):
    volume = 0
    subs = Subsidiaries.objects.filter(id=user.subsidiary_id, location=location)
    if subs:
        for sub in subs:
            sub_trans = Transaction.objects.filter(supplier__company=user.company, supplier__subsidiary_id=sub.id,
                                                is_complete=True)
            for sub_tran in sub_trans:
                volume += sub_tran.offer.quantity
    return volume        


def get_volume_sales_by_location():
    from .constants import zimbabwean_towns, major_cities
    zimbabwean_towns = zimbabwean_towns[1:]
    sales_data_by_city = {}
    sales_data_by_location = {}
    suppliers = User.objects.filter(user_type='SUPPLIER')
    
    for city in zimbabwean_towns:
        city_volume = 0
        for supplier in suppliers:
            city_volume += get_subsidiary_sales_volume_in_city(supplier,city=city)                    
        sales_data_by_city[city] = city_volume    
            
    for major_city in major_cities:
        for city, locations in major_city.items():
            for location in locations:
                loc_volume = 0
                for supplier in suppliers:
                    loc_volume += get_subsidiary_sales_volume_in_location(supplier,location=location)
                sales_data_by_location[str(location) + ', ' +  str(city)] =  loc_volume
             
    return  sales_data_by_city


def calculate_desperate_areas():
    desperate_areas = {}
    suppliers = User.objects.filter(user_type='SUPPLIER')
    for city in zimbabwean_towns:
        for supplier in suppliers:
            sales_per_region = get_subsidiary_sales_volume_in_city(supplier,city=city)
            requests_per_region = get_subsidiary_requests_volume_in_city(supplier,city=city)
            # print(sales_per_region, requests_per_region)         
            if sales_per_region > requests_per_region :
                desperate_areas[city] = get_subsidiary_sales_volume_in_city(supplier,city=city) - get_subsidiary_requests_volume_in_city(supplier,city=city)
    return desperate_areas      
            
        
def desperate():
    from .constants import zimbabwean_towns, major_cities
    
    desperate_cities = {}

    for city in zimbabwean_towns:
        total_transactions = Transaction.objects.filter(buyer__company__city=city).all()
        num_trans_completed_within = 0
        num_trans_completed_outside = 0
        is_desperate = False
        
        for transaction in total_transactions:  
            suppliers = User.objects.filter(user_type='SUPPLIER').all()
            for supplier in suppliers: 
                if transaction.supplier == supplier:
                    subsidiary = Subsidiaries.objects.filter(id=supplier.subsidiary_id).first()
                    if subsidiary != None:
                        if subsidiary.city == city:
                            num_trans_completed_within += transaction.offer.quantity
                        else:
                            num_trans_completed_outside += transaction.offer.quantity
                    else:
                        pass


                else:
                    pass

        if num_trans_completed_outside > num_trans_completed_within:
            is_desperate = True
            deficit = num_trans_completed_outside - num_trans_completed_within
            desperate_cities[city] = deficit


        else:
            pass
    
    return desperate_cities  
    
def get_desperate_cities():
    desperate_cities = {}
    
    for city in major_cities:
        desperate_city = desperate(city)
        if desperate_city:
            desperate_cities[city] = desperate_city[1]
            
    return desperate_cities    



### cfehome.utils.py or the root of your project conf

def get_model_field_names(model, ignore_fields=['content_object']):
    '''
    ::param model is a Django model class
    ::param ignore_fields is a list of field names to ignore by default
    This method gets all model field names (as strings) and returns a list 
    of them ignoring the ones we know don't work (like the 'content_object' field)
    '''
    model_fields = model._meta.get_fields()
    model_field_names = list(set([f.name for f in model_fields if f.name not in ignore_fields]))
    return model_field_names


def get_lookup_fields(model, fields=None):
    '''
    ::param model is a Django model class
    ::param fields is a list of field name strings.
    This method compares the lookups we want vs the lookups
    that are available. It ignores the unavailable fields we passed.
    '''
    model_field_names = get_model_field_names(model)
    if fields is not None:
        '''
        we'll iterate through all the passed field_names
        and verify they are valid by only including the valid ones
        '''
        lookup_fields = []
        for x in fields:
            if "__" in x:
                # the __ is for ForeignKey lookups
                lookup_fields.append(x)
            elif x in model_field_names:
                lookup_fields.append(x)
    else:
        '''
        No field names were passed, use the default model fields
        '''
        lookup_fields = model_field_names
    return lookup_fields

def qs_to_dataset(qs, fields=None):
    '''
    ::param qs is any Django queryset
    ::param fields is a list of field name strings, ignoring non-model field names
    This method is the final step, simply calling the fields we formed on the queryset
    and turning it into a list of dictionaries with key/value pairs.
    '''
    
    lookup_fields = get_lookup_fields(qs.model, fields=fields)
    return list(qs.values(*lookup_fields))

import pandas as pd

def convert_to_dataframe(qs, fields=None, index=None):
    '''
    ::param qs is an QuerySet from Django
    ::fields is a list of field names from the Model of the QuerySet
    ::index is the preferred index column we want our dataframe to be set to
    
    Using the methods from above, we can easily build a dataframe
    from this data.
    '''
    lookup_fields = get_lookup_fields(qs.model, fields=fields)
    index_col = None
    if index in lookup_fields:
        index_col = index
    elif "id" in lookup_fields:
        index_col = 'id'
    values = qs_to_dataset(qs, fields=fields)
    df = pd.DataFrame.from_records(values, columns=lookup_fields, index=index_col)
    return df    
                







                    
                    
                
                
                
            
            
            
                  
            
            
    
    
