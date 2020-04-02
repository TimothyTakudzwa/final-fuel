from django.urls import path

from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('allocations/', views.allocations, name='allocations'),
    path('profile/', views.profile, name='profile'),
    path('orders/', views.orders, name='orders'),
    path('fuel_update/<int:id>', views.fuel_update, name='fuel_update'),
    path('edit_prices/<int:id>', views.edit_prices, name='edit_prices'),
    path('payment_approval/<int:id>', views.payment_approval, name='payment_approval'),
    path('allocate_fuel/<int:id>', views.allocate_fuel, name='allocate_fuel'),
    path('reports/', views.report_generator, name="report_generator"),
    path('statistics/', views.statistics, name="statistics"),
    path('depots/', views.depots, name='depots'),
    path('edit_depot/<int:id>', views.edit_depot, name='edit_depot'),
    path('delete_depot/<int:id>', views.delete_depot, name='delete_depot'),
    path('staff/', views.staff, name='staff'),
    path('activity/', views.activity, name='activity')


]