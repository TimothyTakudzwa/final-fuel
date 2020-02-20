from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('company_fuel/', views.company_fuel, name='company_fuel'),
    path('allocations/<int:id>', views.allocations, name='allocations')
    
]