from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    # path('', views.allocate, name="home"),
    path('audit_trail/', views.audit_trail, name="audit_trail"),
    path('allocated_fuel/<int:sid>', views.allocated_fuel, name="allocatedfuel"),
    path('suppliers/', views.suppliers_list, name="suppliers_list"),
    path('stations/', views.stations, name="stations"),
    path('allocate/', views.allocate, name="allocate"),
    path('allocation_update/<int:id>', views.allocation_update, name="allocation_update"),
    path('depots/', views.depots, name="depots"),
    path('myaccount/', views.myaccount, name="myaccount"),
    path('depot_staff/', views.depot_staff, name="depot_staff"),
    path('export_pdf/', views.export_pdf, name="export_pdf"),
    path('get_pdf/', views.get_pdf, name="get_pdf"),
    # path('generate_pdf/', views.generate_pdf, name="generate_pdf"),
    path('account_activate/', views.account_activate, name="account_activate"),
    path('export_csv/', views.export_csv, name="export_csv"),
    path('statistics/', views.statistics, name="statistics"),
    path('report_generator/', views.report_generator, name="report_generator"),
    path('buyers/', views.buyers_list, name="buyers_list"),
    path('supplier_user_create/<int:sid>', views.supplier_user_create, name="supplier_user_create"),
    path('client_history/<int:cid>', views.client_history, name="client_history"),
    path('subsidiary_transaction_history/<int:sid>', views.subsidiary_transaction_history, name="subsidiary_transaction_history"),
    path('buyer_user_create/<int:sid>', views.buyer_user_create, name="buyer_user_create"),
    path('supplier_user_delete/<int:sid>', views.suppliers_delete, name="suppliers_delete"),
    path('buyer_user_delete/<int:sid>', views.buyers_delete, name="buyers_delete"),
    path('supplier_user_delete/<int:cid>/<int:sid>', views.supplier_user_delete, name="supplier_user_delete"),
    path('supplier_user_edit/<int:cid>', views.supplier_user_edit, name="supplier_user_edit"),
    path('edit_subsidiary/<int:id>', views.edit_subsidiary, name="edit_subsidiary"),
    path('delete_subsidiary/<int:id>', views.delete_subsidiary, name="delete_subsidiary"),
    path('edit_fuel_prices/<int:id>', views.edit_fuel_prices, name="edit_fuel_prices"),
    path('allocate_diesel/<int:id>', views.allocate_diesel, name="allocate_diesel"),
    path('edit_ss_rep/<int:id>', views.edit_ss_rep, name="edit_ss_rep"),
    path('edit_depot_rep/<int:id>', views.edit_depot_rep, name="edit_depot_rep"),
    path('delete_depot_staff/<int:id>', views.delete_depot_staff, name="delete_depot_staff"),
    path('company_profile/', views.company_profile, name="company_profile"),
    path('company_petrol/<int:id>', views.company_petrol, name="company_petrol"),
    path('company_diesel/<int:id>', views.company_diesel, name="company_diesel"),
    path('waiting_for_approval/', views.waiting_for_approval, name="waiting_for_approval"),
    path('approval/<int:id>', views.approval, name="approval"),
    path('decline_applicant/<int:id>', views.decline_applicant, name="decline_applicant"),
    path('edit_allocation/<int:id>', views.edit_allocation, name="edit_allocation"),
    

    

    
    

    
    

   

    
    
    
    
    

    
    



    # path('/index/', views.index, name="home")
    # path('/index/', views.index, name="home")

]