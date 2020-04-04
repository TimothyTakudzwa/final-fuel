from django.db import models
from national.models import Order


class Collections(models.Model):
    has_collected = models.BooleanField(default=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_for_collection')
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    date_collected = models.DateField(null=True, blank=True)
    time_collected = models.TimeField(null=True, blank=True)

    transporter = models.CharField(max_length=150, blank=True, null=True)
    truck_reg = models.CharField(max_length=150, blank=True, null=True)
    trailer_reg = models.CharField(max_length=150, blank=True, null=True)
    driver = models.CharField(max_length=150, blank=True, null=True)
    driver_id = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Collections'
        ordering = ['date', 'time']
