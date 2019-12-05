from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
from .models import Notification


@receiver(post_save, sender=Notification)
def distribute(sender, instance, created, **kwargs):
    if created:
        messages = Notification.objects.get(id=instance.id)
        url = ''
        values = dict(user=messages.name.username, message=messages.message)
        return requests.post(url=url, json=values)

