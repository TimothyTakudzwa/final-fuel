from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views

#from .views import user_profile

urlpatterns = [
    path('', views.fuel_updates, name="home"),
    path('myaccount/', views.myaccount, name='myaccount'),
    path('activate_whatsapp/', views.activate_whatsapp, name='activate_whatsapp'),
    path('allocated_fuel/', views.allocated_fuel, name='allocated_fuel'),
    path('update_diesel/<int:id>', views.update_diesel, name='update_diesel'),
    path('allocated_quantity/', views.allocated_quantity, name='allocated_quantity'),
    


    
]