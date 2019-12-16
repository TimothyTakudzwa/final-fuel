from django.db import models
from buyer.constants2 import COMPANY_CHOICES, INDUSTRY_CHOICES

# from supplier.models import Subsidiaries


# Create your models here.
class FuelUpdate(models.Model):
    sub_type = models.CharField(max_length=255, choices=(('Company', 'Company'), ('Service Station', 'Service Station'), ('Depot', 'Depot')))
    diesel_quantity = models.IntegerField(default=0)
    petrol_quantity = models.IntegerField(default=0)
    last_updated = models.DateField(auto_now_add=True)
    petrol_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    diesel_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    queue_length = models.CharField(max_length=255,choices=(('short', 'Short'), ('medium', 'Medium Long'), ('long', 'Long')))
    deliver = models.BooleanField(default=False)
    cash = models.BooleanField(default=False)
    ecocash = models.BooleanField(default=False)
    swipe = models.BooleanField(default=False)
    usd = models.BooleanField(default=False)
    relationship_id = models.IntegerField()
    company_id = models.IntegerField()
    status = models.CharField(max_length=1000)
    limit = models.FloatField()


    class Meta:
        ordering = ['last_updated']
    
    

class Company(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    industry = models.CharField(max_length=255, choices=INDUSTRY_CHOICES)
    logo = models.ImageField(default='default.png', upload_to='company_profile_logo')
    is_verified = models.BooleanField(default=False)
    company_type = models.CharField(max_length=255, choices=COMPANY_CHOICES)
    fuel_capacity = models.ForeignKey(FuelUpdate, on_delete=models.DO_NOTHING,blank=True, null=True)
    iban_number = models.CharField(max_length=100, default="0")
    license_number = models.CharField(max_length=100, default="0")
    destination_bank = models.CharField(max_length=100, default="0")
    account_number = models.CharField(max_length=100, default="0")
    amount = models.FloatField(default=0.00)
    
    def __str__(self):
        return f'{str(self.id)} - {str(self.name)}'

    @classmethod
    def get_model_by_id(cls, id):
        return cls.objects.filter(id=id).first()

   
