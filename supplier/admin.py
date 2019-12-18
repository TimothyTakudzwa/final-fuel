from django.contrib import admin


from company.models import FuelUpdate

from supplier.models import *

admin.site.site_header = "FuelFinder Super Admin"
admin.site.site_title = 'Admin Portal'
admin.site.index_title = 'FuelFinder Admin'


# admin.site.register(Profile)

admin.site.register(Transaction)
admin.site.register(TokenAuthentication)
admin.site.register(SupplierRating)
admin.site.register(Offer)
admin.site.register(FuelAllocation)
admin.site.register(UserReview)
# admin.site.register(Depot)


