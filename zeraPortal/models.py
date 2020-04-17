from django.db import models


class FuelPrices(models.Model):
    rtgs_diesel_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_diesel_pumpprice = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_diesel_vat = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_diesel_duty = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_diesel_fob = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_diesel_oil_cmargin = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_diesel_dmargin = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_petrol_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_petrol_pumpprice = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_petrol_vat = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_petrol_duty = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_petrol_fob = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_petrol_oil_cmargin = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_petrol_dmargin = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_diesel_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_diesel_pumpprice = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_diesel_vat = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_diesel_duty = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_diesel_fob = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_diesel_oil_cmargin = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_diesel_dmargin = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_pumpprice = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_vat = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_duty = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_fob = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_oil_cmargin = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_dmargin = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_zfms = models.DecimalField(default=0.05, max_digits=10, decimal_places=2)
    rtgs_zfms = models.DecimalField(default=1.00, max_digits=10, decimal_places=2)

   
   
    
    
