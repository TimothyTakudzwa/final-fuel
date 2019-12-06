from django.urls import path, include
from . import views as api


urlpatterns = [

    path('login/', api.login_api, name='login-api'),
    path('login-user/', api.login_user_api, name='login-user-api'),
    path('register/', api.register, name='register-api'),
    path('update-station/', api.update_station_api, name='update-api'),
    path('view-updates/', api.view_station_updates_api, name='view-updates-api'),
    path('view-updates-user/', api.view_updates_user_api, name='view-updates-user-api'),
    path('reset-password/', api.reset_password_api, name='reset-password-api'),
    path('change-password/', api.change_password_api, name='change-password-api'),

]

