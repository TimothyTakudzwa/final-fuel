from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('available_stock/', views.available_stock, name='available_stock'),
    path('supplier/<int:id>', views.offer, name='supplier'),
    path('stock_update/<int:id>', views.stock_update, name='stock_update'),
    path('edit_offer/<int:id>', views.edit_offer, name="edit_offer"),
    path('account/', views.account, name='account'),
    path('mark_completion/<int:id>', views.mark_completion, name='mark_completion'),
    path('payment_history/<int:id>', views.payment_history, name='payment_history'),
    path('my_offers/', views.my_offers, name='my_offers'),
    path('transaction/', views.transaction, name='transaction'),
    path('complete-transaction/<int:id>', views.complete_transaction, name='complete-transaction'),
    path('allocated_quantity/', views.allocated_quantity, name='allocated_quantity'),
    path('activate_whatsapp/', views.activate_whatsapp, name='activate_whatsapp'),
    path('company/', views.company, name='company'),
    path('change_password/', views.change_password, name='change_password'),
    path('initial-password-change/', views.initial_password_change, name='initial-password-change'),
    path('view_invoice/<int:id>', views.view_invoice, name='view_invoice'),
    path('release-note/<int:id>', views.upload_release_note, name='release-note'),
    path('view-release-note/<int:id>', views.view_release_note, name='view-release-note'),
    path('edit-release-note/<int:id>', views.edit_release_note, name='edit-release-note'),
    path('payment-and-release-notes/<int:id>', views.payment_release_notes, name='payment-and-release-notes'),
    path('download-delivery-note/<int:id>', views.view_delivery_note, name='download-delivery-note'),
    path('create-company/<int:id>', views.create_company, name='create_company'),
    path('edit_delivery_schedule/', views.edit_delivery_schedule, name="edit_delivery_schedule"),
    path('delivery_schedules/', views.delivery_schedules, name="delivery_schedules"),
    path('create_delivery_schedule/', views.create_delivery_schedule, name="create_delivery_schedule"),
    path('view_confirmation_doc/<int:id>', views.view_confirmation_doc, name="view_confirmation_doc"),
    path('view_supplier_doc/<int:id>', views.view_supplier_doc, name="view_supplier_doc"),
    path('del_supplier_doc/<int:id>', views.del_supplier_doc, name="del_supplier_doc"),
    path('clients', views.clients, name="clients"),
    path('verify_client/<int:id>', views.verify_client, name="verify_client"),
    path('download-proof/<int:id>', views.download_proof, name="download-proof"),
    path('view_client_id_document/<int:id>', views.view_client_id_document, name="view_client_id_document"),
    path('view_client_application_document/<int:id>', views.view_application_id_document, name="view_application_id_document"),
    path('client_transaction_history/<int:id>', views.client_transaction_history, name="client_transaction_history"),
    path('supplier_release_note/<int:id>', views.supplier_release_note, name='supplier_release_note')


]