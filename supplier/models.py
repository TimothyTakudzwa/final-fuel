from django.db import models
from PIL import Image
from buyer.models import FuelRequest, User
from company.models import Company, FuelUpdate
from buyer.constants import *
from .constants import *
from buyer.constants2 import *

STATUS_CHOICES = (('Open','OPEN'),('Closed','CLOSED'),('Offloading','Offloading'))

class Subsidiaries(models.Model):
    # ADD CLOSING TIME, PAYMENT METHOD 
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default='')
    address = models.CharField(max_length=200, help_text='Harare, Livingstone Street')   
    city = models.CharField(max_length=200, default='', choices=Zimbabwean_Towns)
    location = models.CharField(max_length=200, default='', choices='')
    has_fuel = models.BooleanField(default=False)    
    is_depot = models.BooleanField(default=False)    
    opening_time = models.CharField(max_length=100, default='08:00')
    closing_time = models.CharField(max_length=100, default='22:00')
    fuel_capacity = models.ForeignKey(FuelUpdate, on_delete=models.DO_NOTHING, null=True)
    destination_bank = models.CharField(max_length=100, default="")
    account_number = models.CharField(max_length=100, default="")
    amount = models.FloatField(default=0.00)
    logo = models.ImageField(default='default.png', upload_to='subsidiary_profile_logo')


    def __str__(self):
        return f"{self.name}"

    def get_capacity(self):
        return self.capacity

    def fuel_available(self):
        return self.has_fuel        


class FuelAllocation(models.Model):
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, null=True)
    date = models.DateField(auto_now_add=True)
    diesel_quantity = models.IntegerField(default=0)
    petrol_quantity = models.IntegerField(default=0)
    sub_type = models.CharField(max_length=255)
    cash = models.BooleanField(default=False)
    ecocash = models.BooleanField(default=False)
    swipe = models.BooleanField(default=False)
    usd = models.BooleanField(default=False)
    petrol_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    diesel_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    assigned_staff_id = models.IntegerField(default=0)
    action = models.CharField(max_length=255, default='')



class Offer(models.Model):
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='offer')
    request = models.ForeignKey(FuelRequest, on_delete=models.DO_NOTHING, related_name='request')
    cash = models.BooleanField(default=False, blank=True, null=True)
    ecocash = models.BooleanField(default=False,  blank=True, null=True)
    swipe = models.BooleanField(default=False,  blank=True, null=True)
    usd = models.BooleanField(default=False,  blank=True, null=True)
    delivery_method = models.CharField(max_length=200, default='',  blank=True, null=True)
    collection_address = models.CharField(max_length=200, default='',  blank=True, null=True)
    pump_available = models.BooleanField(default=False,  blank=True, null=True)
    dipping_stick_available = models.BooleanField(default=False,  blank=True, null=True)
    meter_available = models.BooleanField(default=False,  blank=True, null=True)
    declined = models.BooleanField(default=False,  blank=True, null=True)

    class Meta:
        ordering = ['date', 'time']


class TokenAuthentication(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='token_name')
    token = models.CharField(max_length=100)
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['user']

    def __str__(self):
        return str(self.user)


class SupplierRating(models.Model):
    rating = models.PositiveIntegerField(default=0)
    supplier = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='supplier_rating')

    class Meta:
        ordering = ['supplier', 'rating']

    def __str__(self):
        return f'{str(self.supplier)} - {str(self.rating)}'


class Transaction(models.Model):
    supplier = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='supplier')
    offer = models.ForeignKey(Offer, on_delete=models.DO_NOTHING, related_name='offer')
    buyer = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='buyer')
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    
    
    class Meta:
        ordering = ['date', 'time']

class UserReview(models.Model):
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)
    company_type = models.CharField(max_length=255, default= '')
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='company_rating')
    transaction = models.ForeignKey(Transaction, on_delete=models.DO_NOTHING, related_name='transaction')
    rater = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='rater')
    depot = models.ForeignKey(Subsidiaries, on_delete=models.DO_NOTHING, related_name='subsidiary_rating')
    comment = models.CharField(max_length=500, default='')

    def __str__(self):
        return f'{self.rating} - {self.rater}'
