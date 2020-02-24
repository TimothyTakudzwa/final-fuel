from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('company_fuel/', views.company_fuel, name='company_fuel'),
    path('allocations/<int:id>', views.allocations, name='allocations'),
    path('report_generator', views.report_generator, name='report_generator'),
    path('statistics', views.statistics, name='statistics'),
    path('subsidiaries/', views.subsidiaries, name='subsidiaries'),
    path('company-subsidiaries/<int:id>', views.company_subsidiaries, name='company-subsidiaries'),
    path('block_company/<int:id>', views.block_company, name='block_company'),
    path('unblock_company/<int:id>', views.unblock_company, name='unblock_company'),
    path('change_licence/<int:id>', views.change_licence, name='change_licence'),
    path('block_licence/<int:id>', views.block_licence, name='block_licence'),
    path('unblock_licence/<int:id>', views.unblock_licence, name='unblock_licence'),
    path('add_licence/<int:id>', views.add_licence, name='add_licence'),
    path('clients_history/<int:cid>', views.clients_history, name="clients_history"),
    path('subsidiary_transaction_history/<int:sid>', views.subsidiary_transaction_history, name="subsidiary_transaction_history"),
    path('profile/', views.profile, name='profile')
    
    
    
    
]