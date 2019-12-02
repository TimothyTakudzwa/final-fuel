from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('register', views.register, name='buyer-register'),
    path('login', auth_views.LoginView.as_view(template_name='buyer/login.html'), name='buyer-login'),
    path('logout', auth_views.LogoutView.as_view(template_name='buyer/logout.html'), name='buyer-logout'),
    path('profile', views.profile, name='buyer-profile'),
    path('', views.dashboard, name='buyer-dashboard'),
    path('fuel', views.fuel_request, name='fuel-request'),
    path('offers/<int:id>', views.offers, name='fuel-offers'),
    path('login_success/', views.login_success, name='login_success'),
]

if settings.DEBUG: 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

