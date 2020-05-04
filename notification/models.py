from django.db import models
from buyer.models import User
from company.models import Company
from national.models import NoicDepot
from supplier.models import Subsidiaries 


class Notification(models.Model):
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_name', blank = True, null= True)
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, blank=True, null=True)
    message = models.CharField(max_length=5000)
    action = models.CharField(max_length=30, choices=(('REQUEST' , 'REQUEST'), ('OFFER' , 'OFFER'),  ('FOR_FUEL' , 'FOR_FUEL'), ('NEW_SUBSIDIARY' , 'NEW_SUBSIDIARY'), ('DELVERY','DELVERY'),('ORDER', 'ORDER'), ('D-NOTE', 'D-NOTE'), ('MORE_FUEL', 'MORE_FUEL')))
    reference_id = models.PositiveIntegerField(default=0)
    is_read = models.BooleanField(default=False) 
    responsible_depot = models.ForeignKey(NoicDepot, on_delete=models.DO_NOTHING, blank=True, null=True)
    responsible_subsidiary = models.ForeignKey(Subsidiaries, on_delete=models.DO_NOTHING, blank=True, null=True)
    depot_id = models.PositiveIntegerField(default=0) 
    is_noic_depot = models.BooleanField(default=False) 
    handler_id = models.PositiveIntegerField(default=0)

    
    def __str__(self):
        return f'{str(self.user)} - {str(self.date)}'

    class Meta:
        ordering = ['date', 'time', 'user']

    def save(self, *args, **kwargs):
        super(Notification, self).save(*args, **kwargs)

