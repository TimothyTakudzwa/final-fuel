from django.db import models
from PIL import Image
from buyer.models import User, FuelRequest
from company.models import Company, FuelUpdate
from buyer.constants import *

class Subsidiaries(models.Model):
    # ADD CLOSING TIME, PAYMENT METHOD 
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default='')
    address = models.CharField(max_length=200, help_text='Harare, Livingstone Street')    
    has_fuel = models.BooleanField(default=False)    
    opening_time = models.CharField(max_length=100, default='08:00')
    closing_time = models.CharField(max_length=100, default='22:00')
    fuel_capacity = models.ForeignKey(FuelUpdate, on_delete=models.DO_NOTHING, null=True)


    def __str__(self):
        return f"{self.company} : {self.has_fuel}"

    def get_capacity(self):
        return self.capacity

    def fuel_available(self):
        return self.has_fuel        



class Offer(models.Model):
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='offer')
    request = models.ForeignKey(FuelRequest, on_delete=models.DO_NOTHING, related_name='request')

    class Meta:
        ordering = ['quantity']


class TokenAuthentication(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='token_name')
    token = models.CharField(max_length=100)

    class Meta:
        ordering = ['user']

    def __str__(self):
        return str(self.user)


class SupplierRating(models.Model):
    rating = models.PositiveIntegerField(default=0)
    supplier = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='supplier_rating')

    class Meta:
        ordering = ['supplier', 'rating']

    def __str__(self):
        return f'{str(self.supplier)} - {str(self.rating)}'


class Transaction(models.Model):
    request = models.ForeignKey(FuelRequest, on_delete=models.DO_NOTHING, related_name='fuel_request')
    offer = models.ForeignKey(Offer, on_delete=models.DO_NOTHING, related_name='offer')
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f'{str(self.request_name)} - {str(self.buyer_name)}'
