from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [  
    path('logout', auth_views.LogoutView.as_view(template_name='buyer/signin.html'), name='buyer-logout'),
    path('profile', views.profile, name='buyer-profile'),
    path('change_password', views.change_password, name='bchange-password'),
    path('', views.dashboard, name='buyer-dashboard'),
    path('fuel', views.fuel_request, name='buyer-fuel-request'),
    path('offers/<int:id>', views.offers, name='fuel-offers'),
    path('transaction_review/delete/<int:id>', views.transactions_review_delete, name='tran-review-delete'),
    path('transaction_review/edit/<int:id>', views.transaction_review_edit, name='tran-review-edit'),
    path('accept/<int:id>', views.accept_offer, name='accept-offer'),
    path('reject/<int:id>', views.reject_offer, name='reject-offer'),
    path('transactions', views.transactions, name='buyer-transactions'),
    path('delivery-schedule/', views.delivery_schedules, name="delivery-schedule"),
    path('delivery-schedule/<int:id>', views.delivery_schedule, name="delivery-schedule"),
    path('invoice/<int:id>', views.invoice, name='buyer-invoice'),
    path('view_invoice/<int:id>', views.view_invoice, name='view-invoice'),
]

