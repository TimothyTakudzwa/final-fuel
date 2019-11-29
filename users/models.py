from django.db import models
from django.dispatch import receiver
from supplier.models import *
from buyer.models import *
from django.db import models
from django.contrib import messages


class AuditTrail(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    service_station = models.ForeignKey(Subsidiaries, on_delete=models.DO_NOTHING, null=True)
    date = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=700, blank=True)
    reference = models.CharField(max_length=300, blank=True)
    reference_id = models.PositiveIntegerField(default=0)
    
    

