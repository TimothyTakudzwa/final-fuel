from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [  
    path('logout', auth_views.LogoutView.as_view(template_name='buyer/signin.html'), name='buyer-logout'),
    path('profile', views.profile, name='buyer-profile'),
    path('', views.dashboard, name='buyer-dashboard'),
    path('fuel', views.fuel_request, name='buyer-fuel-request'),
    path('offers/<int:id>', views.offers, name='fuel-offers'),
    path('accept/<int:id>', views.accept_offer, name='accept-offer'),
    path('reject/<int:id>', views.reject_offer, name='reject-offer'),
    path('transactions', views.transactions, name='buyer-transactions'),
    path('invoice/<int:id>', views.invoice, name='buyer-invoice'),
    path('login_success/', views.login_success, name='login_success'),
    path('view_invoice/', views.view_invoice, name='view-invoice'),
]

if settings.DEBUG: 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

