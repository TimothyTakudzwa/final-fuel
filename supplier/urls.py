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
    path('my_offers/', views.my_offers, name='my_offers'),
    path('transaction/', views.transaction, name='transaction'),
    path('complete-transaction/', views.complete_transaction, name='complete-transaction'),
    path('allocated_quantity/', views.allocated_quantity, name='allocated_quantity'),
    path('activate_whatsapp/', views.activate_whatsapp, name='activate_whatsapp'),
    path('company/', views.company, name='company'),
    path('change_password/', views.change_password, name='change_password'),
    path('view_invoice/<int:id>', views.view_invoice, name='view_invoice'),
    path('create-company/<int:id>', views.create_company, name='create_company')

]