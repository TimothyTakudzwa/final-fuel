from django.db import models
from company.models import Company
from buyer.models import User

class NationalFuelUpdate(models.Model):
    date = models.DateField(auto_now_add=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    allocated_petrol = models.FloatField(default=0.00)
    allocated_diesel = models.FloatField(default=0.00)
    unallocated_petrol = models.FloatField(default=0.00)
    unallocated_diesel = models.FloatField(default=0.00)
    diesel_price = models.FloatField(default=0.00)
    petrol_price = models.FloatField(default=0.00)

    def __str__(self):
        return f'{self.id} {self.company.name} -- NationalFuelUpdate'


    class Meta:
        ordering = ['company']


class SordNationalAuditTrail(models.Model):
    date = models.DateField(auto_now_add=True)
    sord_no =  models.CharField(max_length=100)
    action_no = models.PositiveIntegerField()
    action = models.CharField(max_length=150)
    fuel_type = models.CharField(max_length=150, blank=True, null=True)
    initial_quantity = models.FloatField(default=0.0)
    quantity_allocated = models.FloatField(default=0.0)
    end_quantity = models.FloatField(default=0.0)
    allocated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='allocated_by_national')
    allocated_to = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='allocated_to_national')
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='company_allocation_national')

    def __str__(self):
        return f'{self.id} -- SordNationalAuditTrail'

