from django.contrib import admin
from buyer.models import User, FuelRequest
from company.models import Company
from supplier.models import Subsidiaries

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username','first_name', 'last_name', 'phone_number')


# Register your models here.
#admin.site.register(Profile)
admin.site.register(User, UserAdmin)
admin.site.register(Company)
admin.site.register(FuelRequest)
admin.site.register(Subsidiaries)
#admin.site.register(Depot)