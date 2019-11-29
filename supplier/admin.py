from django.contrib import admin
from .models import Profile, FuelUpdate, FuelRequest, Transaction, TokenAuthentication, \
    SupplierRating, Offer

from supplier.models import *

admin.site.site_header = "FuelFinder Super Admin"
admin.site.site_title = 'Admin Portal'
admin.site.index_title = 'FuelFinder Admin'


admin.site.register(Profile)
admin.site.register(FuelUpdate)
admin.site.register(FuelRequest)
admin.site.register(Transaction)
admin.site.register(TokenAuthentication)
admin.site.register(SupplierRating)
admin.site.register(Offer)
admin.site.register(FuelAllocation)
# admin.site.register(Depot)


