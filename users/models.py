from supplier.models import *
from buyer.models import *
from supplier.models import *
from django.db import models
from buyer.models import User


class AuditTrail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_station = models.ForeignKey(Subsidiaries, on_delete=models.DO_NOTHING, null=True)
    date = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=700, blank=True)
    reference = models.CharField(max_length=300, blank=True)
    reference_id = models.PositiveIntegerField(default=0)

class SordActionsAuditTrail(models.Model):
    date = models.DateField(auto_now_add=True)
    sord_num = models.CharField(max_length=150, blank=True, null=True)
    action_num = models.IntegerField(default=0)
    allocated_quantity =  models.FloatField(default=0.00)
    allocated_by = models.CharField(max_length=150, blank=True, null=True)
    allocated_to = models.CharField(max_length=150, blank=True, null=True)
    payment_type = models.CharField(max_length=150,default="RTGS")
    fuel_type = models.CharField(max_length=150, blank=True, null=True)
    price = models.FloatField(default=0.00)
    supplied_from = models.CharField(max_length=150, blank=True, null=True)
    action_type = models.CharField(max_length=150, blank=True, null=True)


class Audit_Trail(models.Model):
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_station = models.ForeignKey(Subsidiaries, on_delete=models.DO_NOTHING, null=True)
    date = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=700, blank=True)
    reference = models.CharField(max_length=300, blank=True)
    reference_id = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f'{self.user.username} - {self.company.name}'

