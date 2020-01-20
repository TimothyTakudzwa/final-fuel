from django.db import models
from django.dispatch import receiver

from supplier.models import *
from buyer.models import *
from supplier.models import *

from django.db import models
# from django.contrib.auth.models import User
#from fuelfinder.settings import AUTH_USER_MODEL as User
from buyer.models import User
from django.contrib import messages


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

    
    

