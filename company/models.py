from django.db import models
from buyer.constants2 import COMPANY_CHOICES, INDUSTRY_CHOICES
class Company(models.Model):
    name = models.CharField(max_length=255, default='')
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
    
    def __str__(self):
        return f'{str(self.id)} - {str(self.name)}'

    @classmethod
    def get_model_by_id(cls, id):
        return cls.objects.filter(id=id).first()

   
class CompanyFuelUpdate(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_fuel_update')
    allocated_petrol = models.FloatField(default=0.00)
    allocated_diesel = models.FloatField(default=0.00)
    unallocated_petrol = models.FloatField(default=0.00)
    unallocated_diesel = models.FloatField(default=0.00)
    diesel_price = models.FloatField(default=0.00)
    petrol_price = models.FloatField(default=0.00)

    def __str__(self):
        return f'{self.id} {self.company.name} -- Fuel Update'


    class Meta:
        ordering = ['company']



class SuballocationFuelUpdate(models.Model):
    from supplier.models import Subsidiaries
    subsidiary = models.ForeignKey(Subsidiaries, on_delete=models.CASCADE, related_name='subsidiary_suballocation')
    payment_type = models.CharField(max_length=255, null=True, choices=(('USD', 'USD'), ('RTGS', 'RTGS'), ('USD & RTGS', 'USD & RTGS')))
    queue_length = models.CharField(max_length=255,choices=(('short', 'Short'), ('medium', 'Medium Long'), ('long', 'Long')))
    deliver = models.BooleanField(default=False)
    cash = models.BooleanField(default=False)
    ecocash = models.BooleanField(default=False)
    swipe = models.BooleanField(default=False)
    usd = models.BooleanField(default=False)
    fca = models.BooleanField(default=False)
    last_updated = models.DateField()
    petrol_price = models.FloatField()
    diesel_price = models.FloatField()
    petrol_usd_price = models.FloatField()
    diesel_usd_price = models.FloatField()
    status = models.CharField(max_length=1000)
    limit = models.FloatField()

    def __str__(self):
        return f'{self.id} -- SubAllocation '
