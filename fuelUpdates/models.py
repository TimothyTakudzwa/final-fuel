from django.db import models
from company.models import Company
from buyer.models import User


class SordCompanyAuditTrail(models.Model):
    date = models.DateField(auto_now_add=True)
    sord_no =  models.CharField(max_length=100)
    action_no = models.PositiveIntegerField()
    action = models.CharField(max_length=150)
    fuel_type = models.CharField(max_length=150, blank=True, null=True)
    initial_quantity = models.FloatField(default=0.0)
    quantity_allocated = models.FloatField(default=0.0)
    end_quantity = models.FloatField(default=0.0)
    allocated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='allocated_by')
    allocated_to = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='allocated_by')
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='company_sord')

    def __str__(self):
        return f'{self.id} -- SordCompanyAuditTrail'

   class Meta:
        ordering = ['date']
     

