from django.urls import path

from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('allocations/', views.allocations, name='allocations'),
    path('profile/', views.profile, name='profile')
]