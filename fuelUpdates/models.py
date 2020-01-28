from django.db import models
from company.models import Company
from buyer.models import User


class CompanyFuelUpdate(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_fuel_update_model', null=True)
    allocated_petrol = models.FloatField(default=0.00)
    allocated_diesel = models.FloatField(default=0.00)
    unallocated_petrol = models.FloatField(default=0.00)
    unallocated_diesel = models.FloatField(default=0.00)
    diesel_price = models.FloatField(default=0.00)
    petrol_price = models.FloatField(default=0.00)

    def __str__(self):
        return f'{self.id} {self.company.name} -- Fuel Update'


    class Meta:
        ordering = ['company']



class SordCompanyAuditTrail(models.Model):
    sord_no =  models.CharField(max_length=100)
    action_no = models.PositiveIntegerField()
    action = models.CharField(max_length=150)
    initial_quantity = models.FloatField(default=0.0)
    quantity_allocated = models.FloatField(default=0.0)
    end_quantity = models.FloatField(default=0.0)
    allocated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='allocated_by')
    allocated_to = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='allocated_by')
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='company_sord')

    def __str__(self):
        return f'{self.id} -- SordCompanyAuditTrail'
     

