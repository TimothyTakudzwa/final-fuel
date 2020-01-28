from django.db import models
from company.models import Company
# Create your models here.
class CompanyFuelUpdate(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
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



class SuballocationFuelUpdate(models.Model):
    from supplier.models import Subsidiaries
    subsidiary = models.ForeignKey(Subsidiaries, on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=255, null=True, choices=(('USD', 'USD'), ('RTGS', 'RTGS'), ('USD & RTGS', 'USD & RTGS')))
    queue_length = models.CharField(max_length=255,choices=(('short', 'Short'), ('medium', 'Medium Long'), ('long', 'Long')))
    deliver = models.BooleanField(default=False)
    cash = models.BooleanField(default=False)
    ecocash = models.BooleanField(default=False)
    swipe = models.BooleanField(default=False)
    usd = models.BooleanField(default=False)
    fca = models.BooleanField(default=False)
    last_updated = models.DateField()
    petrol_price = models.FloatField()
    diesel_price = models.FloatField()
    petrol_usd_price = models.FloatField()
    diesel_usd_price = models.FloatField()
    status = models.CharField(max_length=1000)
    limit = models.FloatField()

    def __str__(self):
        return f'{self.id}, SubAllocation '


class SubsidiaryFuelUpdate(models.Model):
    from supplier.models import Subsidiaries
    subsidiary = models.ForeignKey(Subsidiaries, on_delete=models.CASCADE)
    petrol_quantity = models.FloatField(default=0.0)
    diesel_quantity = models.FloatField(default=0.0)
    company_update = models.ForeignKey(CompanyFuelUpdate)
    last_updated = models.DateField()
    

    def __str__(self):
        return f'{self.id} -- SubsidiaryFuelUpdate ' 


class SordCompanyAuditTrail(models.Model):
    sord_no =  models.CharField(max_length=100)
    action_no = models.PositiveIntegerField()
    action = models.CharField(max_length=150)
    initial_quantity = models.FloatField(default=0.0)
    quantity_allocated = models.FloatField(default=0.0)
    end_quantity = models.FloatField(default=0.0)
    allocated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    allocated_to = models.ForeignKey(Company, on_delete=models.DO_NOTHING)
    company = models.ForeignKey(company, on_delete=models.DO_NOTHING)

    def __str__(self):
        return f'{self.id} -- SordCompanyAuditTrail'
     

