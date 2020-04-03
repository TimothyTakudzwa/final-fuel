from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Collections
from national.models import Order


@receiver(post_save, sender=Order)
def orders_log(sender, instance, created, **kwargs):
    if created:
        order = Order.objects.get(id=instance.id)
        Collections.objects.create(
            order=order,
        )
