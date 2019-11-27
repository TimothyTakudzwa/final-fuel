from django.contrib import admin
from .models import AuditTrail
from supplier.models import Depot

# Register your models here.
admin.site.register(AuditTrail)
admin.site.register(Depot)

