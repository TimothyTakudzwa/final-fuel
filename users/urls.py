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
    path('allocation_update_main/<int:id>', views.allocation_update_main, name="allocation_update_main"),
    path('sord_allocations/', views.sord_allocations, name="sord_allocations"),
    path('depots/', views.depots, name="depots"),
    path('myaccount/', views.myaccount, name="myaccount"),
    path('depot_staff/', views.depot_staff, name="depot_staff"),
    path('get_pdf/', views.get_pdf, name="get_pdf"),
    # path('generate_pdf/', views.generate_pdf, name="generate_pdf"),
    path('account_activate/', views.account_activate, name="account_activate"),
    path('statistics/', views.statistics, name="statistics"),
    path('client-application/', views.client_application, name="client-application"),
    path('download-application/<int:id>', views.download_application, name="download-application"),
    path('download-document/<int:id>', views.download_document, name="download-document"),
    path('download-tax-clearance/<int:id>', views.download_tax_clearance, name="download-tax-clearance"),
    path('download-cr14/<int:id>', views.download_cr14, name="download-cr14"),
    path('download-cr6/<int:id>', views.download_cr6, name="download-cr6"),
    path('download-cert-of-inc/<int:id>', views.download_cert_of_inc, name="download-cert-of-inc"),
    path('download-proof-of-residence/<int:id>', views.download_proof_of_residence, name="download-proof-of-residence"),
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
    path('application-approval/<int:id>', views.application_approval, name="application-approval"),
    path('edit_suballocation_fuel_prices/<int:id>', views.edit_suballocation_fuel_prices, name="edit_suballocation_fuel_prices"),
    path('sordactions/<id>', views.sordactions, name="sordactions"),
    path('sord_station_sales/', views.sord_station_sales, name="sord_station_sales"),
    path('edit_ss_rep/<int:id>', views.edit_ss_rep, name="edit_ss_rep"),
    path('edit_depot_rep/<int:id>', views.edit_depot_rep, name="edit_depot_rep"),
    path('delete_depot_staff/<int:id>', views.delete_depot_staff, name="delete_depot_staff"),
    path('company_profile/', views.company_profile, name="company_profile"),
    path('company_petrol/<int:id>', views.company_petrol, name="company_petrol"),
    path('company_diesel/<int:id>', views.company_diesel, name="company_diesel"),
    path('waiting_for_approval/', views.waiting_for_approval, name="waiting_for_approval"),
    path('approval/<int:id>', views.approve_applicant, name="approval"),
    path('decline_applicant/<int:id>', views.decline_applicant, name="decline_applicant"),
    path('edit_allocation/<int:id>', views.edit_allocation, name="edit_allocation"),
    path('upload_users/', views.upload_users, name='upload_users'),
    path('place_order/', views.place_order, name='place_order'),
    path('orders/', views.orders, name='orders'),
    path('view_release_note/<int:id>', views.view_release_note, name='view_release_note'),
    path('delivery_note/<int:id>', views.delivery_note, name='delivery_note'),
    path('download_proof/<int:id>', views.download_proof, name='download_proof')

]