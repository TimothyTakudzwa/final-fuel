from django.urls import path, include
from . import  views as api

urlpatterns = [
    path('login-api/', api.login_api, name='login-api'),
    path('logout-api/', api.logout_api, name='logout-api'),
    path('update-station-api/', api.update_station_api, name='login-api'),
    path('view-station-updates-api/', api.view_station_updates_api, name='login-api'),
]
