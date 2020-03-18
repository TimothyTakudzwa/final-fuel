from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('company_fuel/', views.company_fuel, name='company_fuel'),
    path('allocations/<int:id>', views.allocations, name='allocations'),
    path('report_generator/', views.report_generator, name='report_generator'),
    path('statistics/', views.statistics, name='statistics'),
    path('subsidiaries/', views.subsidiaries, name='subsidiaries'),
    path('company-subsidiaries/<int:id>', views.company_subsidiaries, name='company-subsidiaries'),
    path('block_company/<int:id>', views.block_company, name='block_company'),
    path('add-supplier-admin/<int:id>', views.add_supplier_admin, name='add-supplier-admin'),
    path('unblock_company/<int:id>', views.unblock_company, name='unblock_company'),
    path('change_licence/<int:id>', views.change_licence, name='change_licence'),
    path('block_licence/<int:id>', views.block_licence, name='block_licence'),
    path('unblock_licence/<int:id>', views.unblock_licence, name='unblock_licence'),
    path('add_licence/<int:id>', views.add_licence, name='add_licence'),
    path('clients_history/<int:cid>', views.clients_history, name="clients_history"),
    path('subsidiary_transaction_history/<int:sid>', views.subsidiary_transaction_history, name="subsidiary_transaction_history"),
    path('profile/', views.profile, name='profile'),
    path('sordactions/<id>', views.sordactions, name='sordactions'),
    path('transactions/<int:id>', views.transactions, name='transactions'),
    path('payment_and_schedules/<int:id>', views.payment_and_schedules, name='payment_and_schedules'),
    path('view_confirmation_doc/<int:id>', views.view_confirmation_doc, name='view_confirmation_doc'),
    path('view_supplier_doc/<int:id>', views.view_supplier_doc, name='view_supplier_doc'),
    path('suspicious_behavior/', views.suspicious_behavior, name='suspicious_behavior'),
    path('desperate-regions/', views.desperate_regions, name='desperate-regions'),
    path('download_release_note/<int:id>', views.download_release_note, name='download_release_note'),
    path('download_application/<int:id>', views.download_application, name='download_application'),
    path('download_fire_brigade_doc/<int:id>', views.download_fire_brigade_doc, name='download_fire_brigade_doc'),
    path('download_ema/<int:id>', views.download_ema, name='download_ema'),
    path('download_council/<int:id>', views.download_council, name='download_council'),
    path('download_pop/<int:id>', views.download_pop, name='download_pop'),
    path('edit-company-details/<int:id>', views.edit_company, name='edit-company-details'),
    
    
]
