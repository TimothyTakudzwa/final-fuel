from django.contrib import admin
from .models import NationalFuelUpdate, SordNationalAuditTrail, Order, NoicDepot, DepotFuelUpdate
# Register your models here.
admin.site.register(NationalFuelUpdate)
admin.site.register(SordNationalAuditTrail)
admin.site.register(Order)
admin.site.register(NoicDepot)
admin.site.register(DepotFuelUpdate)
