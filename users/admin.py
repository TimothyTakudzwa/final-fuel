from django.contrib import admin
from .models import Audit_Trail, SordActionsAuditTrail
# from supplier.models import Depot

# Register your models here.
admin.site.register(Audit_Trail)
admin.site.register(SordActionsAuditTrail)

