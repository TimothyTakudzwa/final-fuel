from django.db import models
# from fuelfinder.settings import AUTH_USER_MODEL as User
from .constants2 import * 
from PIL import Image
from django.contrib.auth.models import AbstractUser
from company.models import Company




class User(AbstractUser):
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, null=True)
    fuel_request = models.PositiveIntegerField(default=0)
    phone_number = models.CharField(max_length=20, default='263')
    stage = models.CharField(max_length=20, default='registration')
    company_position = models.CharField(max_length=100, default='')
    position = models.IntegerField(default=0)
    user_type = models.CharField(max_length=20, default='', choices=TYPE_CHOICES)
    image = models.ImageField(default='default.png', upload_to='buyer_profile_pics')
    activated_for_whatsapp = models.BooleanField(default=False)
    subsidiary_id = models.IntegerField(default=0)
    #fuel_updates_ids = models.CharField(max_length=2000, default=0)


    def __str__(self):
        return f'{self.username}'
    
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
    fuel_type = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=200)
    delivery_method = models.CharField(max_length=200)
    delivery_address = models.CharField(max_length=200, default='', null=True)
    storage_tanks = models.CharField(max_length=20, default='', choices=STORAGE_TANKS)
    pump_required = models.BooleanField(default=False)
    dipping_stick_required = models.BooleanField(default=False)
    meter_required = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    is_direct_deal = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    wait = models.BooleanField(default=False)
    last_deal = models.IntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    cash = models.BooleanField(default=False)
    ecocash = models.BooleanField(default=False)
    swipe = models.BooleanField(default=False)
    usd = models.BooleanField(default=False)

    class Meta:
        ordering = ['date', 'time', 'name']

    def __str__(self):
        return f'{str(self.name)}'

