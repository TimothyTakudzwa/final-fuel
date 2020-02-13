from django.db import models

# Create your models here.
from buyer.models import User
from company.models import Company
from supplier.models import Transaction


class Account(models.Model):
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    buyer_company = models.ForeignKey(Company, on_delete=models.DO_NOTHING,blank=True, null=True ,related_name='buyer_name')
    supplier_company = models.ForeignKey(Company, on_delete=models.DO_NOTHING,blank=True, null=True, related_name='supplier_name')
    applied_by = models.ForeignKey(User, on_delete=models.DO_NOTHING,blank=True, null=True, related_name='applicant')
    account_number = models.CharField(max_length=100, default='', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    application_document = models.FileField(upload_to='applications', blank=True)
    id_document = models.FileField(upload_to='id_documents', blank=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f'{str(self.buyer_company.name)}'


class AccountHistory(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='account_history')
    balance = models.FloatField(default=0)
    sord_number = models.CharField(max_length=255, null=True, blank=True)
    proof_of_payment = models.FileField(null=True, upload_to='proof_of_payment', blank=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='transaction_account_history')
    value = models.FloatField(help_text='proof of payment value', null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f'{str(self.account.buyer_company.name)} - ${str(self.balance)}'

