from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('stock/', views.stock, name='stock'),
    path('upload_release_note/<int:id>', views.upload_release_note, name='upload_release_note'),
    path('profile/', views.profile, name='profile')
]