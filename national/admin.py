from django.contrib import admin
from .models import NationalFuelUpdate, SordNationalAuditTrail, Order
# Register your models here.
admin.site.register(NationalFuelUpdate)
admin.site.register(SordNationalAuditTrail)
admin.site.register(Order)
