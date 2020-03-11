from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('stock/', views.stock, name='stock'),
    path('profile/', views.profile, name='profile')
]