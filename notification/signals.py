from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
from .models import Notification
from supplier.models import Offer
from buyer.models import FuelRequest


@receiver(post_save, sender=Notification)
def distribute(sender, instance, created, **kwargs):
    if created:
        messages = Notification.objects.get(id=instance.id)
        
        msg = ''

        if messages.action == "REQUEST":
            fuel_request = FuelRequest.objects.get(id=messages.reference_id)
            msg = f'Hello {messages.user.username},  {fuel_request.name} has requested for {fuel_request.amount}l of {fuel_request.fuel_type}'
        elif messages.action == "OFFER":
            offer = Offer.objects.get(id=messages.reference_id)
            msg = f'Hello {messages.user.username} {offer.supplier.username} is selling fuel at ${offer.price}'


        url = 'https://dreamhub.co.zw/notify'
        values = dict(user_id=messages.user.id, notification=msg, action=messages.action)
        return requests.post(url=url, json=values)

