from django.db import models

# Create your models here.
from buyer.models import User
from company.models import Company


class Account(models.Model):
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    buyer_company = models.ForeignKey(Company, on_delete=models.DO_NOTHING,blank=True, null=True ,related_name='buyer_name')
    supplier_company = models.ForeignKey(Company, on_delete=models.DO_NOTHING,blank=True, null=True, related_name='supplier_name')
    account_number = models.CharField(max_length=100, default='', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    application_document = models.FileField(upload_to='applications')

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f'{str(self.buyer_company.name)}'


