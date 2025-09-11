from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Vehicle, VehicleImage, Booking, Payment

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_verified_driver', 'is_staff')

class VehicleImageInline(admin.TabularInline):
    model = VehicleImage
    extra = 1

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('brand','model_name','vehicle_type','price_per_hour','price_per_day','is_active')
    inlines = [VehicleImageInline]

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('vehicle','user','start_time','end_time','status','total_price')
    list_filter = ['status', 'start_time', 'user']   # Added filters for better admin usability

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'booking',
        'amount',
        'status',
        'transaction_id',
        'stripe_session_id',
        'stripe_payment_intent',
        'created_at',
    )
    