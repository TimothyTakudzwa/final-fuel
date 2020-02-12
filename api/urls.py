from django.urls import path
from . import views as api


urlpatterns = [

    path('login/', api.login),
    path('login-user/', api.login_user),

    path('register/', api.register),

    path('update-station/', api.update_station),
    path('view-updates/', api.view_station_updates),
    path('view-updates-user/', api.view_updates_user),

    path('view-profile/', api.get_profile),

    path('reset-password/', api.password_reset),
    path('change-password/', api.change_password),
    path('force-password-change/', api.force_password_change),

    path('view-comments/', api.view_comments),
    path('update-comments/', api.update_comments),

]

