from django.db import models
from PIL import Image
from buyer.models import User, FuelRequest, Company
from buyer.constants import *

class ServiceStation(models.Model):
    # ADD CLOSING TIME, PAYMENT METHOD 
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default='')
    address = models.CharField(max_length=200, help_text='Harare, Livingstone Street')
    capacity = models.PositiveIntegerField(default=0)
    has_fuel = models.BooleanField(default=False)
    stock_petrol = models.FloatField(help_text='Volume In Litres')
    stock_diesel = models.FloatField(help_text='Volume In Litres')
    closing_time = models.CharField(max_length=100, default='22:00')
    payment_method = models.CharField(max_length=100, choices=PAYING_CHOICES)

    def __str__(self):
        return f"{self.company} : {self.has_fuel}"

    def get_capacity(self):
        return self.capacity

    def fuel_available(self):
        return self.has_fuel        

class Depot(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default='')
    address = models.CharField(max_length=200, help_text='Harare, Livingstone Street')
    capacity = models.PositiveIntegerField(default=0)
    has_fuel = models.BooleanField(default=False)
    stock_petrol = models.FloatField(help_text='Volume In Litres')
    stock_diesel = models.FloatField(help_text='Volume In Litres')
    closing_time = models.CharField(max_length=100, default='22:00')
    payment_method = models.CharField(max_length=100, choices=PAYING_CHOICES)

    def __str__(self):
        return f"{self.company} : {self.name}"

    def get_capacity(self):
        return self.capacity

    def fuel_available(self):
        return self.has_fuel        




class Profile(models.Model):
    name = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    picture = models.ImageField(default='default.png', upload_to='profiles')
    phone = models.CharField(max_length=20, help_text='eg 263775580596')  
    position_in_company = models.CharField(max_length=255)
    is_authorized = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.picture.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.picture.path)

    class Meta:
        ordering = ['name']

class FuelUpdate(models.Model):
    # To Do Add Type For Bulk Or Individual
    supplier = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='supplier_name')
    closing_time = models.TimeField()
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fuel_type = models.CharField(max_length=20)
    deliver = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=200)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['date', 'time', 'supplier']

    def __str__(self):
        return f'{str(self.supplier)} - {str(self.max_amount)}l'


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
