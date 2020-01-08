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
    name = models.CharField(max_length=255, default='')
    address = models.CharField(max_length=255, default='')
    industry = models.CharField(max_length=255,  default='', choices=INDUSTRY_CHOICES)
    logo = models.ImageField(blank=True, null=True,default='default.png', upload_to='company_profile_logo')
    is_verified = models.BooleanField(default=False)
    company_type = models.CharField(max_length=255, default='',choices=COMPANY_CHOICES, blank=True, null=True)
    fuel_capacity = models.ForeignKey(FuelUpdate, on_delete=models.DO_NOTHING,blank=True, null=True)
    iban_number = models.CharField(max_length=100, default='', blank=True, null=True)
    license_number = models.CharField(max_length=100, default='', blank=True, null=True)
    destination_bank = models.CharField(max_length=100, default='', blank=True, null=True)
    account_number = models.CharField(max_length=100, default='', blank=True, null=True)
    amount = models.FloatField(default=0.00, blank=True, null=True)
    
    def __str__(self):
        return f'{str(self.id)} - {str(self.name)}'

    @classmethod
    def get_model_by_id(cls, id):
        return cls.objects.filter(id=id).first()

   
