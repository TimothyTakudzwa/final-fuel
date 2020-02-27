from django.db import models
from django.contrib.auth.models import AbstractUser
from PIL import Image

from .constants2 import *
from company.models import Company

"""

Custom User Model

"""


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
    is_waiting = models.BooleanField(default=False)
    subsidiary_id = models.IntegerField(default=0)
    fuel_updates_ids = models.CharField(max_length=2000, default=0)
    password_reset = models.BooleanField(default=False)
    paying_method = models.CharField(max_length=2000, default=0)

    def __str__(self):
        return f'{self.username}'

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)


"""

Fuel Request Model

"""


class FuelRequest(models.Model):
    """
    last deal is tied to a specific subsidiary.
    """
    name = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    supplier_company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, blank=True, null=True)
    amount = models.IntegerField(default=0)
    fuel_type = models.CharField(max_length=50)
    delivery_method = models.CharField(max_length=200)
    delivery_address = models.CharField(max_length=200, blank=True, null=True)
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
    payment_method = models.CharField(max_length=255, null=True, choices=(('USD', 'USD'), ('RTGS', 'RTGS'),
                                                                          ('USD & RTGS', 'USD & RTGS')))
    cash = models.BooleanField(default=False)
    ecocash = models.BooleanField(default=False)
    swipe = models.BooleanField(default=False)
    usd = models.BooleanField(default=False)
    private_mode = models.BooleanField(default=False)

    class Meta:
        ordering = ['date', 'time', 'name']
