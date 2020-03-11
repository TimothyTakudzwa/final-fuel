from django.urls import path

from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('allocations/', views.allocations, name='allocations'),
    path('profile/', views.profile, name='profile'),
    path('orders/', views.orders, name='orders'),
    path('rtgs_update/<int:id>', views.rtgs_update, name='rtgs_update'),
    path('usd_update/<int:id>', views.usd_update, name='usd_update'),
    path('edit_prices/<int:id>', views.edit_prices, name='edit_prices'),
    path('payment_approval/<int:id>', views.payment_approval, name='payment_approval'),
    path('allocate_fuel/<int:id>', views.allocate_fuel, name='allocate_fuel'),
    path('reports/', views.report_generator, name="report_generator"),
    path('statistics/', views.statistics, name="statistics"),
    path('staff/', views.staff, name='staff')


]