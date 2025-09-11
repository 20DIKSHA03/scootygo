from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vehicle, VehicleImage, Booking, Payment
from django.utils import timezone

User = get_user_model()

# -------------------------
# User serializers
# -------------------------
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ('id','username','email','password','phone_number','driving_license_number','license_doc')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username','email','phone_number','driving_license_number','is_verified_driver','license_doc')
        read_only_fields = ('is_verified_driver',)

    def validate_license_doc(self, file):
        max_size = 5 * 1024 * 1024  # 5MB limit
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png']

        if file.size > max_size:
            raise serializers.ValidationError("File too big. Max size allowed is 5MB.")
        if file.content_type not in allowed_types:
            raise serializers.ValidationError("Unsupported file type. Allowed types: PDF, JPG, PNG.")
        return file

# -------------------------
# Vehicle serializers
# -------------------------
class VehicleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleImage
        fields = ('id','image')

class VehicleSerializer(serializers.ModelSerializer):
    images = VehicleImageSerializer(many=True, read_only=True)

    class Meta:
        model = Vehicle
        fields = ('id','vehicle_type','brand','model_name','plate_number','description',
                  'price_per_hour','price_per_day','is_active','images')

# -------------------------
# Booking serializer
# -------------------------
class BookingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    vehicle = serializers.PrimaryKeyRelatedField(queryset=Vehicle.objects.filter(is_active=True))
    vehicle_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Booking
        fields = ('id','user','vehicle','vehicle_display','start_time','end_time','total_price','status','created_at')
        read_only_fields = ('total_price','status','created_at','user','vehicle_display')

    def get_vehicle_display(self, obj):
        return f"{obj.vehicle.brand} {obj.vehicle.model_name}"

    def validate(self, data):
        start = data.get('start_time')
        end = data.get('end_time')

        if not start or not end:
            raise serializers.ValidationError("start_time and end_time are required.")
        if end <= start:
            raise serializers.ValidationError("end_time must be after start_time.")
        if start < timezone.now():
            raise serializers.ValidationError("start_time cannot be in the past.")
        return data

# -------------------------
# Payment serializer (mock)
# -------------------------
class PaymentSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())

    class Meta:
        model = Payment
        fields = ('id','booking','amount','transaction_id','status','created_at')
        read_only_fields = ('created_at',)

