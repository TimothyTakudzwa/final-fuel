from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
from .models import Notification
from supplier.models import Offer
from buyer.models import FuelRequest

@receiver(post_save, sender=Notification)
def distribute(sender, instance, created, **kwargs):
    if created:
        messages = Notification.objects.filter(id=instance.id).first()
        
        if messages.action == "new_request":
            #domain = request.get_host()
            click_url = f'https://fuelfinderzim.com/new_fuel_request/{messages.reference_id}'
            url = 'https://dreamhub.co.zw/notify'
            values = dict(user_id=messages.user.id, notification=messages.message, action=messages.action,url = click_url)
            return requests.post(url=url, json=values)
        elif messages.action == "new_offer":
            #domain = request.get_host()
            click_url = f'https://fuelfinderzim.com/new_fuel_offer/{messages.reference_id}'
            url = 'https://dreamhub.co.zw/notify'
            values = dict(user_id=messages.user.id, notification=messages.message, action=messages.action,url = click_url)
            return requests.post(url=url, json=values)
        elif messages.action == "offer_accepted":
            #domain = request.get_host()
            click_url = f'https://fuelfinderzim.com/accepted_offer/{messages.reference_id}'
            url = 'https://dreamhub.co.zw/notify'
            values = dict(user_id=messages.user.id, notification=messages.message, action=messages.action,url = click_url)
            return requests.post(url=url, json=values)
        elif messages.action == "offer_rejected":
            #domain = request.get_host()
            click_url = f'https://fuelfinderzim.com/rejected_offer/{messages.reference_id}'
            url = 'https://dreamhub.co.zw/notify'
            values = dict(user_id=messages.user.id, notification=messages.message, action=messages.action,url = click_url)
            return requests.post(url=url, json=values)
        elif messages.action == 'DELIVERY':
            click_url = f'https://fuelfinderzim.com/view_delivery_schedule/{messages.reference_id}'
            url = 'https://dreamhub.co.zw/notify'
            values = dict(user_id=messages.user.id, notification=messages.message, action=messages.action,url = click_url)
            return requests.post(url=url, json=values)
        elif messages.action == 'schedule':
            click_url = f'https://fuelfinderzim.com/delivery_schedule/{messages.reference_id}'
            url = 'https://dreamhub.co.zw/notify'
            values = dict(user_id=messages.user.id, notification=messages.message, action=messages.action,url = click_url)
            return requests.post(url=url, json=values)


       
