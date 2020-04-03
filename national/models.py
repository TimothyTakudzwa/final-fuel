from django.db import models
from company.models import Company
from buyer.models import User
from supplier.constants import Zimbabwean_Towns


class NoicDepot(models.Model):
    name = models.CharField(max_length=150, blank=True, null=True)
    address = models.CharField(max_length=200, help_text='Harare, Livingstone Street')
    city = models.CharField(max_length=200, default='', choices=Zimbabwean_Towns)
    has_fuel = models.BooleanField(default=False)
    opening_time = models.CharField(max_length=100, default='08:00')
    closing_time = models.CharField(max_length=100, default='22:00')
    destination_bank = models.CharField(max_length=100, default="")
    account_number = models.CharField(max_length=100, default="")
    logo = models.ImageField(default='default.png', upload_to='subsidiary_profile_logo')
    license_num = models.CharField(max_length=150, blank=True, null=True)
    praz_reg_num = models.CharField(max_length=150, blank=True, null=True)
    bp_num = models.CharField(max_length=150, blank=True, null=True)
    vat = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    ema = models.FileField(upload_to='subsidiary_docs', blank=True, null=True)
    fire_brigade = models.FileField(upload_to='subsidiary_docs', blank=True, null=True)
    application_form = models.FileField(upload_to='subsidiary_docs', blank=True, null=True)
    bank_branch = models.CharField(max_length=500, null=True, blank=True)


class Order(models.Model):
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0.00)
    fuel_type = models.CharField(max_length=150, blank=True, null=True)
    currency = models.CharField(max_length=255, null=True, choices=(('USD', 'USD'), ('RTGS', 'RTGS')))
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    proof_of_payment = models.FileField(upload_to='proof_of_payment', null=True, blank=True)
    payment_approved = models.BooleanField(default=False)
    allocated_fuel = models.BooleanField(default=False)
    amount_paid = models.DecimalField(max_digits=20, default=0.00, decimal_places=2)
    duty = models.DecimalField(max_digits=20, default=0.00, decimal_places=2)
    vat = models.DecimalField(max_digits=20, default=0.00, decimal_places=2)
    transporter = models.CharField(max_length=150, blank=True, null=True)
    truck_reg = models.CharField(max_length=150, blank=True, null=True)
    trailer_reg = models.CharField(max_length=150, blank=True, null=True)
    driver = models.CharField(max_length=150, blank=True, null=True)
    driver_id = models.CharField(max_length=150, blank=True, null=True)
    noic_depot = models.ForeignKey(NoicDepot, on_delete=models.DO_NOTHING, related_name='company_allocation',
                                   blank=True, null=True)

    class Meta:
        ordering = ['-date', '-time']


class NationalFuelUpdate(models.Model):
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True, null=True)
    allocated_petrol = models.FloatField(default=0.00)
    allocated_diesel = models.FloatField(default=0.00)
    unallocated_petrol = models.FloatField(default=0.00)
    unallocated_diesel = models.FloatField(default=0.00)
    diesel_price = models.DecimalField(max_digits=10, default=0.00, decimal_places=2)
    petrol_price = models.DecimalField(max_digits=10, default=0.00, decimal_places=2)
    currency = models.CharField(max_length=255, null=True, choices=(('USD', 'USD'), ('RTGS', 'RTGS')))

    class Meta:
        ordering = ['-date', '-time']


class SordNationalAuditTrail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.DO_NOTHING, related_name='company_order', blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True, null=True)
    sord_no = models.CharField(max_length=100, blank=True, null=True)
    action_no = models.PositiveIntegerField(blank=True, null=True)
    action = models.CharField(max_length=150, blank=True, null=True)
    fuel_type = models.CharField(max_length=150, blank=True, null=True)
    currency = models.CharField(max_length=255, null=True, choices=(('USD', 'USD'), ('RTGS', 'RTGS')))
    quantity = models.FloatField(default=0.00)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    initial_quantity = models.FloatField(default=0.00)
    quantity_allocated = models.FloatField(default=0.00)
    end_quantity = models.FloatField(default=0.00)
    allocated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='allocated_by_national',
                                     blank=True, null=True)
    allocated_to = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='allocated_to_national',
                                     blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='company_allocation_national',
                                blank=True, null=True)
    assigned_depot = models.ForeignKey(NoicDepot, on_delete=models.DO_NOTHING,
                                       related_name='company_allocation_national', blank=True, null=True)
    release_date = models.DateField(auto_now_add=False, null=True, blank=True)
    release_note = models.BooleanField(default=False)
    d_note = models.FileField(blank=True, null=True, upload_to='proof_of_payment')

    def __str__(self):
        return f'{self.id} -- SordNationalAuditTrail'

    class Meta:
        ordering = ['-date', '-time']


class DepotFuelUpdate(models.Model):
    depot = models.ForeignKey(NoicDepot, on_delete=models.CASCADE, blank=True, null=True)
    usd_petrol = models.FloatField(default=0.00)
    usd_diesel = models.FloatField(default=0.00)
    rtgs_petrol = models.FloatField(default=0.00)
    rtgs_diesel = models.FloatField(default=0.00)
    rtgs_diesel_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rtgs_petrol_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_diesel_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    usd_petrol_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    status = models.CharField(max_length=1000, blank=True, null=True)
