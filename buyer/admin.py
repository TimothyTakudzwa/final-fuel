from django.contrib import admin
<<<<<<< HEAD
from buyer.models import User, Company, FuelRequest
from supplier.models import ServiceStation, Depot
=======
from buyer.models import User, FuelRequest
from company.models import Company
from supplier.models import Subsidiaries
>>>>>>> eb9dae185ddf257ba2a5fdec3e02a1c963ef3c37

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username','first_name', 'last_name', 'phone_number')


# Register your models here.
#admin.site.register(Profile)
admin.site.register(User, UserAdmin)
admin.site.register(Company)
admin.site.register(FuelRequest)
admin.site.register(Subsidiaries)
#admin.site.register(Depot)