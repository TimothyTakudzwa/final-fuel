from django.db import models
from national.models import Order


class Collections(models.Model):
    has_collected = models.BooleanField(default=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_for_collection')
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Collections'
        ordering = ['date', 'time']
