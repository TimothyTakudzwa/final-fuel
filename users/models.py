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

