from django.contrib import admin

#
# from company.models import FuelUpdate

from supplier.models import *

admin.site.site_header = "FuelFinder Super Admin"
admin.site.site_title = 'Admin Portal'
admin.site.index_title = 'FuelFinder Admin'


# admin.site.register(Profile)

class FuelUpdatetAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ( 'id',  'sub_type', 'entry_type', 'diesel_quantity', 'petrol_quantity', 'petrol_price', 'diesel_price',  'company_id','relationship_id')

admin.site.register(Transaction)
admin.site.register(SubsidiaryFuelUpdate)
admin.site.register(TokenAuthentication) 
admin.site.register(SupplierRating)
admin.site.register(Offer)
admin.site.register(FuelAllocation)
admin.site.register(UserReview)
admin.site.register(SuballocationFuelUpdate)
admin.site.register(SordSubsidiaryAuditTrail)
admin.site.register(DeliverySchedule)


