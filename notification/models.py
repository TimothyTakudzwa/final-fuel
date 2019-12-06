from django.db import models
from buyer.models import User


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='notification_name')
    message = models.CharField(max_length=5000)
    is_read = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f'{str(self.user)} - {str(self.date)}'

    class Meta:
        ordering = ['date', 'time']

    def save(self, *args, **kwargs):
        super(Notification, self).save(*args, **kwargs)

