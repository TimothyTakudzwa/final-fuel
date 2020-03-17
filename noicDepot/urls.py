from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('stock/', views.stock, name='stock'),
    path('upload_release_note/<int:id>', views.upload_release_note, name='upload_release_note'),
    path('view_release_note/<int:id>', views.view_release_note, name='view_release_note'),
    path('orders/', views.orders, name='orders'),
    path('allocate_fuel/<int:id>', views.allocate_fuel, name='allocate_fuel'),
    path('profile/', views.profile, name='profile')
]