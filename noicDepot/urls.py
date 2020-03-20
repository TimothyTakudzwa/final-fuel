from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('stock/', views.stock, name='stock'),
    path('upload_release_note/<int:id>', views.upload_release_note, name='upload_release_note'),
    path('view_release_note/<int:id>', views.view_release_note, name='view_release_note'),
    path('orders/', views.orders, name='orders'),
    path('allocate_fuel/<int:id>', views.allocate_fuel, name='allocate_fuel'),
    path('payment_approval/<int:id>', views.payment_approval, name='payment_approval'),
    path('download_proof/<int:id>', views.download_proof, name='download_proof'),
    path('download_d_note/<int:id>', views.download_d_note, name='download_d_note'),
    path('profile/', views.profile, name='profile'),
    path('report_generator/', views.report_generator, name='report_generator'),
    path('statistics/', views.statistics, name='statistics'),

]