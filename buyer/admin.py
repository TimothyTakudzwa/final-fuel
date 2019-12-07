from django.contrib import admin
from buyer.models import User, FuelRequest
from company.models import Company
from supplier.models import Subsidiaries
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username','first_name', 'last_name', 'phone_number', 'user_type')


class FuelRequestAdmin(admin.ModelAdmin):

    list_per_page = 10
    list_display = ('__str__', 'amount', 'fuel_type', 'payment_method' ,'delivery_method', 'date','delivery_address',
    'pump_required','dipping_stick_required', 'meter_required',  'is_direct_deal', 'wait', 'is_complete', 'usd',  'cash', 'ecocash', 'swipe')

# Register your models here.
#admin.site.register(Profile)
admin.site.register(User, UserAdmin)
admin.site.register(Company)
admin.site.register(FuelRequest, FuelRequestAdmin)
admin.site.register(Subsidiaries)
#admin.site.register(Depot)