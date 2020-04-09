from django.db import models


class FuelPrices(models.Model):
    rtgs_diesel_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_diesel_vat = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_diesel_duty = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_petrol_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_petrol_vat = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_petrol_duty = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_diesel_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_diesel_vat = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_diesel_duty = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_vat = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_duty = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    
