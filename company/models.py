from django.db import models
from buyer.constants2 import COMPANY_CHOICES, INDUSTRY_CHOICES


# Create your models here.


class FuelUpdate(models.Model):
    sub_type = models.CharField(max_length=255, choices=(('company', 'Company'), ('service_station', 'Service Station'), ('depot', 'Depot')))
    diesel_quantity = models.IntegerField(default=0)
    petrol_quantity = models.IntegerField(default=0)
    last_updated = models.DateField(auto_now_add=True)
    payment_methods = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deliver = models.BooleanField(default=False)
    relationship_id = models.IntegerField()

    class Meta:
        ordering = ['last_updated']

    def __str__(self):
        return f'{str(self.sub_type)} - Diesel {str(self.diesel_quantity)}. Petrol Quantity {str(self.petrol_quantity)}'

class Company(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    industry = models.CharField(max_length=255, choices=INDUSTRY_CHOICES)
    is_verified = models.BooleanField(default=False)
    company_type = models.CharField(max_length=255, choices=COMPANY_CHOICES)
    fuel_capacity = models.ForeignKey(FuelUpdate, on_delete=models.DO_NOTHING, null=True)
    
    def __str__(self):
        return self.name