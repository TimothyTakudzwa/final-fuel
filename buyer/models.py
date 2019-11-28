from django.db import models
# from fuelfinder.settings import AUTH_USER_MODEL as User
from .constants2 import * 
from PIL import Image
from django.contrib.auth.models import AbstractUser

class Company(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    industry = models.CharField(max_length=255, choices=INDUSTRY_CHOICES)
    is_verified = models.BooleanField(default=False)
    company_type = models.CharField(max_length=255, choices=COMPANY_CHOICES)
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, null=True)
    fuel_request = models.PositiveIntegerField(default=0)
    phone_number = models.CharField(max_length=20, default='263')
    stage = models.CharField(max_length=20, default='registration')
    company_position = models.CharField(max_length=100, default='')
    position = models.IntegerField(default=0)
    user_type = models.CharField(max_length=20, default='', choices=TYPE_CHOICES)
    image = models.ImageField(default='default.png', upload_to='buyer_profile_pics')
    # supplier_role = models.CharField(max_length=70)
    activated_for_whatsapp = models.BooleanField(default=False)

    def __str__(self):
        return f' {self.id} - {self.username}'
    
    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300,300)
            img.thumbnail(output_size)
            img.save(self.image.path) 


class FuelRequest(models.Model):
    name = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    amount = models.IntegerField(default=0)
    split = models.BooleanField(default=False)
    fuel_type = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=200)
    delivery_method = models.CharField(max_length=200)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    is_direct_deal = models.BooleanField(default=False)
    last_deal = models.IntegerField(default=0)

    class Meta:
        ordering = ['date', 'time', 'name']

    def __str__(self):
        return f'{str(self.name)} - {str(self.amount)}'


class Profile(models.Model):
    name = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer_name')
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='company_profile')
    fuel_request = models.OneToOneField(FuelRequest, on_delete=models.CASCADE, related_name='fuel', null=True)
    phone_number = models.CharField(max_length=20, default='')
    stage = models.CharField(max_length=20, default='registration')
    position = models.IntegerField(default=0)
    image = models.ImageField(default='default.png', upload_to='buyer_profile_pics')
    

    def __str__(self):
        return f' {self.name.username} Profile '

    def save(self, *args, **kwargs):
        super(Profile, self).save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300,300)
            img.thumbnail(output_size)
            img.save(self.image.path)    

    class Meta:
        ordering = ['name']

