from django.db import models
from buyer.constants2 import COMPANY_CHOICES, INDUSTRY_CHOICES

# from supplier.models import Subsidiaries


# Create your models here.
class FuelUpdate(models.Model):
    sub_type = models.CharField(max_length=255, choices=(('company', 'Company'), ('service_station', 'Service Station'), ('depot', 'Depot')))
    diesel_quantity = models.IntegerField(default=0)
    petrol_quantity = models.IntegerField(default=0)
    last_updated = models.DateField(auto_now_add=True)
    payment_methods = models.CharField(max_length=20)
    petrol_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    diesel_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    queue_length = models.CharField(max_length=255,choices=(('short', 'Short'), ('medium', 'Medium Long'), ('long', 'Long')))
    deliver = models.BooleanField(default=False)
    relationship_id = models.IntegerField()
    company_id = models.IntegerField()

    class Meta:
        ordering = ['last_updated']
    
    

class Company(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    industry = models.CharField(max_length=255, choices=INDUSTRY_CHOICES)
    is_verified = models.BooleanField(default=False)
    company_type = models.CharField(max_length=255, choices=COMPANY_CHOICES)
    fuel_capacity = models.ForeignKey(FuelUpdate, on_delete=models.DO_NOTHING, null=True)
    
    def __str__(self):
        return self.name
   