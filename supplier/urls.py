from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('fuel_update/', views.fuel_update, name='fuel_update'),
    path('supplier/<int:id>', views.offer, name='supplier'),
    path('edit_offer/<int:id>', views.edit_offer, name="edit_offer"),
    path('account/', views.account, name='account'),

]