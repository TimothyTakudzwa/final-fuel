import random
import faker

from buyer.models import User, FuelRequest
from supplier.models import Offer, Transaction


# initiate faker
faker = faker.Faker()

#variables
buyers = User.objects.filter(user_type='BUYER')
suppliers = User.objects.filter(user_type='SUPPLIER')
fuel_type = ['Petrol', 'Diesel']
delivery_method = ['Self Collection', 'Delivery']
STORAGE_TANKS = ['ABOVE GROUND','BELOW GROUND']
CURRENCIES = ['USD', 'RTGS']



def generate_requests(num):
    created = 0
    requests = []

    for n in range(num):
        r = FuelRequest.objects.create(
            name=random.choice(buyers),
            amount = random.randint(50,1500),
            fuel_type = random.choice(fuel_type),
            delivery_address = faker.address(),
            storage_tanks = random.choice(STORAGE_TANKS),
            pump_required = random.choice((True,False)),
            dipping_stick_required = random.choice((True,False)),
            meter_required = random.choice((True,False)),
            wait=True,
            payment_method=random.choice(CURRENCIES),
            is_test_data = True
        )
        requests.append(r)

        created += 1

    print(f'Finished Creating {created} Requests\nNow generating offers...')
    generate_offers(requests)

def generate_offers(requests):
    created = 0 
    offers = []

    for request in requests:
        offer = Offer.objects.create(
            quantity = random.randint(int((request.amount/4)), request.amount),
            price = round(random.uniform(8,36),2),
            transport_fee = round(random.uniform(10,50),2),
            supplier = random.choice(suppliers),
            request = request,
            cash = random.choice((True,False)),
            ecocash = random.choice((True,False)),
            delivery_method=request.delivery_method,
            is_accepted = True,
        )
        offers.append(offer)

        created += 1

    print(f'Finished Creating {created} Offers\nNow generating transactions...')
    generate_transactions(offers)

def generate_transactions(offers):
    created = 0

    for offer in offers:
        Transaction.objects.create(
            supplier = offer.supplier,
            offer = offer,
            buyer = offer.request.name,
            is_complete=True,
        )
    
        created += 1 
    print(f'Finished Creating {created} Transactions.')


def generate_test_data(num):
    generate_requests(num)


def purge_test_data():
    
    transactions = Transaction.objects.filter(offer__request__is_test_data=True)
    offers = Offer.objects.filter(request__is_test_data=True)
    requests = FuelRequest.objects.filter(is_test_data=True)
    
    print(f'Deleting {transactions.count()} dummy transactions...')
    for tran in transactions:
        tran.delete()

    print(f'Now Deleting {offers.count()} dummy offers...')
    for offer in offers:
        offer.delete()

    print(f'Now Deleting {requests.count()} dummy requests...')
    for request in requests:
        request.delete()
    print("Finished Deleting Data........:)")    
    

        







    
