# rentals/api_views.py
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db import transaction
import math
from django.utils import timezone

from .models import Vehicle, Booking, Payment
from .serializers import (
    VehicleSerializer, BookingSerializer,
    UserRegisterSerializer, UserSerializer
)

User = get_user_model()

# -------------------------
# Vehicle endpoints
# -------------------------
class VehicleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vehicle.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = VehicleSerializer
    permission_classes = [AllowAny]

# -------------------------
# User registration & profile
# -------------------------
class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

# -------------------------
# Booking endpoints
# -------------------------
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all().order_by('-created_at')
        return Booking.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        vehicle = serializer.validated_data['vehicle']
        start = serializer.validated_data['start_time']
        end = serializer.validated_data['end_time']

        hours = (end - start).total_seconds() / 3600.0
        total_price = vehicle.price_per_hour * math.ceil(hours)

        with transaction.atomic():
            v = Vehicle.objects.select_for_update().get(pk=vehicle.pk)
            overlapping_exists = Booking.objects.filter(
                vehicle=v,
                status__in=['PENDING','CONFIRMED','ONGOING'],
                start_time__lt=end,
                end_time__gt=start
            ).exists()
            if overlapping_exists:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"detail": "Vehicle not available in this time range."})

            booking = serializer.save(user=user, total_price=total_price, status='PENDING')
            Payment.objects.create(booking=booking, amount=total_price, status='PENDING')
