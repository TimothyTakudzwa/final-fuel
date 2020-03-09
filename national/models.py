from django.db import models
from company.models import Company
from buyer.models import User


class Order(models.Model):
    date = models.DateField(auto_now_add=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0.00)
    fuel_type = models.CharField(max_length=150, blank=True, null=True)
    currency = models.CharField(max_length=255, null=True, choices=(('USD', 'USD'), ('RTGS', 'RTGS')))
    proof_of_payment = models.FileField(upload_to='proof_of_payment', null=True, blank=True)
    payment_approved = models.BooleanField(default=False)
    allocated_fuel = models.BooleanField(default=False)
class NationalFuelUpdate(models.Model):
    date = models.DateField(auto_now_add=True)
    allocated_petrol = models.FloatField(default=0.00)
    allocated_diesel = models.FloatField(default=0.00)
    unallocated_petrol = models.FloatField(default=0.00)
    unallocated_diesel = models.FloatField(default=0.00)
    diesel_price = models.DecimalField(max_digits=10, default=0.00, decimal_places=2)
    petrol_price = models.DecimalField(max_digits=10, default=0.00, decimal_places=2)
    currency = models.CharField(max_length=255, null=True, choices=(('USD', 'USD'), ('RTGS', 'RTGS')))


class SordNationalAuditTrail(models.Model):
    date = models.DateField(auto_now_add=True)
    sord_no =  models.CharField(max_length=100)
    action_no = models.PositiveIntegerField()
    action = models.CharField(max_length=150)
    fuel_type = models.CharField(max_length=150, blank=True, null=True)
    currency = models.CharField(max_length=255, null=True, choices=(('USD', 'USD'), ('RTGS', 'RTGS')))
    quantity = models.FloatField(default=0.00)
    initial_quantity = models.FloatField(default=0.0)
    quantity_allocated = models.FloatField(default=0.0)
    end_quantity = models.FloatField(default=0.0)
    allocated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='allocated_by_national')
    allocated_to = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='allocated_to_national')
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='company_allocation_national')

    def __str__(self):
        return f'{self.id} -- SordNationalAuditTrail'

