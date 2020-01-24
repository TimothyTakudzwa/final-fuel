from django.contrib import admin
from .models import FuelUpdate
# Register your models here.
class FuelUpdatetAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ( 'id',  'sub_type', 'entry_type', 'diesel_quantity', 'petrol_quantity', 'petrol_price', 'diesel_price',  'company_id','relationship_id')


admin.site.register(FuelUpdate, FuelUpdatetAdmin)