from django.contrib import admin

from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from buyer.models import User, FuelRequest, DeliveryBranch
from company.models import Company
from supplier.models import Subsidiaries


"""

User Admin 

"""


class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'email', 'username', 'first_name', 'last_name', 'phone_number', 'user_type')
    search_fields = ('email', 'username')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'user_type', 'image',)}),
        ('Whatsapp', {
            'fields': (
                'activated_for_whatsapp', 'stage', 'position'),
        }),
        ('Company Details', {
            'fields': (
                'company', 'company_position', 'subsidiary_id', 'fuel_updates_ids', 'fuel_request'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'password_reset', 'is_waiting'),
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )


"""

FuelRequest Admin 

"""


class FuelRequestAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ('__str__', 'amount', 'fuel_type', 'delivery_method', 'date', 'delivery_address',
                    'pump_required', 'dipping_stick_required', 'meter_required', 'is_direct_deal', 'wait',
                    'is_complete', 'usd', 'cash', 'ecocash', 'swipe')


"""

Subsidiaries Admin 

"""


class SubsidiariesAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ('id', 'name')

"""

Delivery Branch Admin 

"""


class DeliveryBranchAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ('id', 'name', 'street_number', 'street_name', 'city')


admin.site.register(User, UserAdmin)
admin.site.register(Company)
admin.site.register(FuelRequest, FuelRequestAdmin)
admin.site.register(DeliveryBranch, DeliveryBranchAdmin)
admin.site.register(Subsidiaries, SubsidiariesAdmin)
admin.site.unregister(Group)
