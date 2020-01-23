from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views as finder_views
import supplier.views as supplier_views
import whatsapp.views as whatsapp_views
import buyer.views as buyer_views
# import finder.views as finder_views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('buyer/', include('buyer.urls')),
    path('api/', include('api.urls')),
    path('register', buyer_views.register, name='buyer-register'),
    path('admin/', admin.site.urls), 
    path('', finder_views.landing_page, name='home'), 
    path('logout/', auth_views.LogoutView.as_view(template_name='supplier/accounts/logout.html'), name='logout'),
    path('password-change/', supplier_views.change_password, name='change-password'),
    path('login/',  auth_views.LoginView.as_view(template_name='buyer/signin.html'), name='login'),
    path('account/', supplier_views.account, name='account'),
    path('fuel-request/', supplier_views.fuel_request, name='fuel-request'),
    path('new_fuel_request/<id>', supplier_views.new_fuel_request, name='new_fuel_request'),
    path('offer_accepted/<id>', supplier_views.offer_accepted, name='offer_accepted'),
    path('new_fuel_offer/<id>', buyer_views.new_fuel_offer, name='new_fuel_offer'),
    path('accepted_offer/<id>', supplier_views.accepted_offer, name='accepted_offer'),
    path('stock_update/<int:id>', supplier_views.stock_update, name='stock_update'),
    path('rejected_offer/<id>', supplier_views.rejected_offer, name='rejected_offer'),
    path('new_offer/<id>', buyer_views.new_offer, name='new_offer'),
    path('verification/<token>/<user_id>', supplier_views.verification, name='verification'),
    path('index', whatsapp_views.index, name='index'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='supplier/password/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='supplier/password/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='supplier/password/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='supplier/password/password_reset_complete.html'),
         name='password_reset_complete'),
    path('users/', include(('users.urls','users'), namespace='users')),
    path('buyer/', include(('buyer.urls','buyer'), namespace='buyer')),
    path('supplier/', include(('supplier.urls','supplier'), namespace='supplier')),
    path('serviceStation/', include(('serviceStation.urls','serviceStation'), namespace='serviceStation')),
    path('available_stock/', supplier_views.available_stock, name='available_stock'),
    path('transaction/', supplier_views.transaction, name='transaction'),
    path('allocated_quantity/', supplier_views.allocated_quantity, name='allocated_quantity'),
    path('my_offers/', supplier_views.my_offers, name='my_offers'),
    path('company/', supplier_views.company, name='company'),
    path('activate_whatsapp/', supplier_views.activate_whatsapp, name='activate_whatsapp'),
    path('change_password/', supplier_views.change_password, name='change_password'),
    path('view_invoice/<int:id>', supplier_views.view_invoice, name='view_invoice'),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

