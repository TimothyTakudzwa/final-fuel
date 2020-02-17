from django.core.management.base import BaseCommand
from django.core.mail import mail_managers
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, datetime
from django.core.mail import BadHeaderError, EmailMultiAlternatives

from supplier.models import DeliverySchedule
from notification.models import Notification


class Command(BaseCommand):
    """
    This command will filter for overdue schedules that haven't issued a reminder and the send
    emails to relevant parties
    """
    help = "Checking and Processing SMS Queue"

    def handle(self, *args, **options):
        self.stdout.write("Checking For Late Delivery schedules...")
        self.stdout.write("Queuing up Notifications For Sending...")
        self.process_delivery_schedules()
        self.stdout.write("Finished Sending Notifications")

    def process_delivery_schedules(self):
        schedules = DeliverySchedule.objects.filter(date__lt=datetime.today(), confirmation_document__isnull=True,
                                                    supplier_document__isnull=True)
        if schedules:
            for delivery in schedules:
                message = f'Please Note That Your Delivery To {delivery.transaction.buyer.company.name.title()} Is ' \
                          f'Late As Of {delivery.date.strftime("%D")} '

                # send email
                sender = f'Fuel Finder Accounts Accounts<{settings.EMAIL_HOST_USER}>'
                title = f'Delivery Schedule Reminder'
                message = f"Dear {delivery.transaction.supplier.first_name}, this is mail serves to inform you " \
                          f"that the due date for the delivery of {delivery.transaction.offer.request.amount}L of {delivery.transaction.offer.request.fuel_type} to {delivery.transaction.buyer.company.name.title()} has elapsed as of {delivery.date.strftime('%A the %dth of %b %Y')}\n." \
                          f"Kindly see to it that concerned parties are informed and that the delivery is secure and it's whereabouts are known.\n\n" \
                          f"Driver Details\n Name: {delivery.driver_name}\n Phone:{delivery.phone_number}"
                f"You can extend due date on this page https://fuelfinderzim.com//supplier/delivery_schedules/"

                # send email
            try:
                msg = EmailMultiAlternatives(title, message, sender, [delivery.transaction.supplier.email])
                msg.send()
            # if error occurs
            except BadHeaderError:
                pass
                # error log should be created

            # Notification.objects.create(message=message, reference_id=delivery.id, action="schedule_reminder")
            self.stdout.write(f"Sending Reminder To {delivery.transaction.supplier.username.title()} Regarding A Late "
                              f"Delivery Date As Of {delivery.date.strftime('%a')}")
            delivery.save()
        else:
            self.stdout.write("Nothing To Process")
