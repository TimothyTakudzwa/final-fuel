import random
import faker

from buyer.models import User, FuelRequest
from company.models import Company
from supplier.models import Offer, Transaction
from buyer.constants2 import INDUSTRY_CHOICES



'''
Scripts to generate test data for statistics. To create test data. Offers, Requests, Transactions. 
- Run `generate_test_data(num)` with num being the number of records you wish to generate. Eg generate_test_data(100)
  will create 100 Requests, Buyers, Sellers, Offers and Transactions.
- To view the current number of test data in the database run `test_data_population()`.
- To see the number of dummy users in the database run `show_faker_user_population()`.
- To purge the whole system of test data run. `purge_test_data`.
'''


# initiate faker
faker = faker.Faker()

#variables
fuel_type = ['Petrol', 'Diesel']
delivery_method = ['Self Collection', 'Delivery']
STORAGE_TANKS = ['ABOVE GROUND','BELOW GROUND']
CURRENCIES = ['USD', 'RTGS']
user_types = ['SUPPLIER','BUYER']


def show_faker_user_population():
    # function to display all fake users
    fake_buyers = User.objects.filter(is_test_data=True, user_type = 'BUYER')
    fake_suppliers = User.objects.filter(is_test_data=True, user_type = 'SUPPLIER')

    print(f"Total population: {fake_buyers.count()+fake_suppliers.count()}\nBuyers: {fake_buyers.count()}\nSuppliers: {fake_suppliers.count()}")


def delete_fake_users():
    fake_users = User.objects.filter(is_test_data=True)
    fake_companies = [user.company for user in fake_users ]
    count = fake_users.count()

    if fake_users:
        print(f"Deleting {count} users and companies from system")
        for user in fake_users: 
            user.delete()
        for company in fake_companies:
            company.delete()
        print(f"No more dummy users in system")
    else:
        print("Nothing to purge")        
        

def create_fake_company(bool):
    # function to create fake companies
    if bool:
        c = Company.objects.create(
            name = faker.company(),
            city = faker.city(),
            industry = random.choice(INDUSTRY_CHOICES),
            company_type = 'CORPORATE BUYER',
            iban_number = faker.uuid4(),
            phone_number = faker.phone_number(),
            is_active = True
        )
    else:
        c = Company.objects.create(
            name = faker.company(),
            city = faker.city(),
            industry = random.choice(INDUSTRY_CHOICES),
            company_type = 'SUPPLIER',
            iban_number = faker.uuid4(),
            phone_number = faker.phone_number(),
            is_active = True
        )
    return c        


def create_users(num):
    suppliers_count = 0
    buyers_count = 0
    for i in range(num):
        b = User.objects.create(
                first_name = faker.first_name(),
                last_name = faker.last_name(),
                username = faker.user_name(),
                password = faker.password(),
                email = faker.email(),
                user_type = 'BUYER',
                company = create_fake_company(True),
                is_test_data = True,
            )
        buyers_count += 1
        f = open('passwords.txt','a')
        f.write(f"{b.username} - {b.password}\n")
        f.close()
        s = User.objects.create(
                first_name = faker.first_name(),
                last_name = faker.last_name(),
                username = faker.user_name(),
                password = faker.password(),
                email = faker.email(),
                user_type = 'SUPPLIER',
                company = create_fake_company(False),
                is_test_data = True,
            )
        suppliers_count += 1
        f = open('passwords.txt','a')
        f.write(f"{s.username} - {s.password} - {s.user_type}\n")
        f.close()
    
    print(f'Finished Creating {suppliers_count} Sellers and {buyers_count} Buyers ...')        
            

def generate_requests(num):
    created = 0
    requests = []

    create_users(num)
    buyers = User.objects.filter(user_type='BUYER', is_test_data=True)
    
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
    suppliers = User.objects.filter(user_type='SUPPLIER', is_test_data=True)

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

    delete_fake_users()

def test_data_population():
    transactions = Transaction.objects.filter(offer__request__is_test_data=True)
    offers = Offer.objects.filter(request__is_test_data=True)
    requests = FuelRequest.objects.filter(is_test_data=True)
    fake_users = User.objects.filter(is_test_data=True)
    fake_companies = [user.company for user in fake_users ]

    print(f'Total Test Data Population\nTransactions: {transactions.count()}\nOffers: {offers.count()}\nRequests: {requests.count()}\nUsers: {fake_users.count()}\nCompanies: {len(fake_companies)}')        
    

        







    
