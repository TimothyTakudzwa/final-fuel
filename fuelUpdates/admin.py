from django.contrib import admin
from .models import SordCompanyAuditTrail, CompanyFuelUpdate

# Register your models here.
admin.site.register(SordCompanyAuditTrail)
admin.site.register(CompanyFuelUpdate)

