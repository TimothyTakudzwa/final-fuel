from django.db import models
from buyer.constants2 import COMPANY_CHOICES, INDUSTRY_CHOICES


class Company(models.Model):
    name = models.CharField(max_length=255, default='')
    city = models.CharField(max_length=150, blank=True, null=True)
    address = models.CharField(max_length=255, default='')
    industry = models.CharField(max_length=255,  default='', choices=INDUSTRY_CHOICES)
    logo = models.ImageField(blank=True, null=True,default='default.png', upload_to='company_profile_logo')
    is_verified = models.BooleanField(default=False)
    company_type = models.CharField(max_length=255, default='',choices=COMPANY_CHOICES, blank=True, null=True)
    #fuel_capacity = models.ForeignKey(CompanyFuelUpdate, on_delete=models.DO_NOTHING,blank=True, null=True)
    iban_number = models.CharField(max_length=100, default='', blank=True, null=True)
    license_number = models.CharField(max_length=100, default='', blank=True, null=True)
    destination_bank = models.CharField(max_length=100, default='', blank=True, null=True)
    account_number = models.CharField(max_length=100, default='', blank=True, null=True)
    amount = models.FloatField(default=0.00, blank=True, null=True)
    bp_num = models.CharField(max_length=100, blank=True, null=True)
    is_govnt_org = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    application_form = models.FileField(upload_to='company_app_forms', null=True, blank=True)
    contact_person = models.CharField(max_length=500, null=True, default='')
    vat_number = models.CharField(max_length=500, null=True, default='')
    phone_number = models.CharField(max_length=500, null=True, default='')

    
    def __str__(self):
        return f'{str(self.name)}'

    @classmethod
    def get_model_by_id(cls, id):
        return cls.objects.filter(id=id).first()

    # @classmethod
    # def get_all_subsidiaries(cls, id):
    #     from supplier.models import Subsidiaries
    #     return Subsidiaries.objects.filter(company=self)

   
class CompanyFuelUpdate(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_fuel_update')
    allocated_petrol = models.FloatField(default=0.00)
    allocated_diesel = models.FloatField(default=0.00)
    unallocated_petrol = models.FloatField(default=0.00)
    unallocated_diesel = models.FloatField(default=0.00)
    usd_diesel_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    diesel_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    petrol_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.id} {self.company.name} -- Fuel Update'


    class Meta:
        ordering = ['company']
