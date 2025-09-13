# rentals/models.py
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    driving_license_number = models.CharField(max_length=50, blank=True, null=True)
    license_doc = models.FileField(upload_to='licenses/', blank=True, null=True)
    is_verified_driver = models.BooleanField(default=False)  # admin toggles

    def __str__(self):
        return self.username

class Vehicle(models.Model):
    TYPE_CHOICES = (('scooty','Scooty'), ('bike','Bike'))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_vehicles')
    vehicle_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    brand = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    plate_number = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2)
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model_name} ({self.vehicle_type})"

class VehicleImage(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='images')
    # For demo: use URLField instead of ImageField
    image = models.URLField()

    def __str__(self):
        return f"Image for {self.vehicle}"

class Booking(models.Model):
    STATUS = (
        ('PENDING','Pending'),
        ('CONFIRMED','Confirmed'),
        ('ONGOING','Ongoing'),
        ('COMPLETED','Completed'),
        ('CANCELLED','Cancelled'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='bookings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle} booked by {self.user} from {self.start_time} to {self.end_time}"

# Updated Payment model with provider info, refund tracking, and improved statuses
# rentals/models.py (only the Payment class shown; keep other models as is)
class Payment(models.Model):
    STATUS_CHOICES = (
        ('PENDING','PENDING'),
        ('SUCCESS','SUCCESS'),
        ('FAILED','FAILED'),
    )
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=200, blank=True, null=True)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')  # PENDING / SUCCESS / FAILED
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.amount} for {self.booking} - {self.status}"
