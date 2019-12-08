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
    path('rate-supplier/', supplier_views.rate_supplier, name='rate-supplier'),
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
    path('supplier/', include(('supplier.urls','supplier'), namespace='supplier')),
    path('serviceStation/', include(('serviceStation.urls','serviceStation'), namespace='serviceStation')),
    path('fuel_update/', supplier_views.fuel_update, name='fuel_update'),
    path('transaction/', supplier_views.transaction, name='transaction'),
    path('allocated_quantity/', supplier_views.allocated_quantity, name='allocated_quantity'),
    path('change_password/', supplier_views.change_password, name='change_password'),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

