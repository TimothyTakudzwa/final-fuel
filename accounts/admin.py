from django.contrib import admin

from .models import Account, AccountHistory


admin.site.register(Account)
admin.site.register(AccountHistory)

