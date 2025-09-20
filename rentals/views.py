from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse

import math
import stripe
import time

from .models import Vehicle, Booking, Payment
from .serializers import (
    VehicleSerializer, BookingSerializer,
    UserRegisterSerializer, UserSerializer
)
from .email_utils import (
    send_booking_confirmation_email,
    send_booking_cancelled_email,
)
from .stripe_utils import STRIPE_PUBLISHABLE_KEY, DOMAIN, STRIPE_WEBHOOK_SECRET

User = get_user_model()


# -------------------------
# Vehicle list / detail
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
    parser_classes = [MultiPartParser, FormParser]  # allow file uploads

    def get_object(self):
        return self.request.user


# -------------------------
# Booking
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
        hours_ceil = math.ceil(hours)
        total_price = vehicle.price_per_hour * hours_ceil

        with transaction.atomic():
            v = Vehicle.objects.select_for_update().get(pk=vehicle.pk)
            overlapping_exists = Booking.objects.filter(
                vehicle=v,
                status__in=['PENDING', 'CONFIRMED', 'ONGOING'],
                start_time__lt=end,
                end_time__gt=start
            ).exists()
            if overlapping_exists:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"non_field_errors": ["Vehicle is not available for the selected time range."]})

            booking = serializer.save(user=user, total_price=total_price, status='PENDING')
            Payment.objects.create(booking=booking, amount=total_price, status='PENDING')

    @action(detail=True, methods=['POST'])
    def cancel(self, request, pk=None):
        """
        Cancel a booking (user or admin).
        Rules:
         - Only owner (or admin) can cancel.
         - Booking must be PENDING or CONFIRMED.
         - If start_time already passed → cannot cancel.
         - If within 24h of start_time → penalty (20%).
        """
        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

        # permissions
        if not (request.user == booking.user or request.user.is_staff):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        if booking.status == 'CANCELLED':
            return Response({"detail": "Booking already cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        if booking.end_time < timezone.now():
            return Response({"detail": "Past bookings cannot be cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        if booking.status not in ['PENDING', 'CONFIRMED']:
            return Response({"detail": "Only PENDING or CONFIRMED bookings can be cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        # check late cancellation
        now = timezone.now()
        time_diff = booking.start_time - now
        late_threshold = timezone.timedelta(hours=24)
        late = time_diff <= late_threshold

        refund_info = {"refunded": 0, "penalty": 0}
        payment = getattr(booking, "payment", None)

        if payment and payment.status == "SUCCESS":
            penalty = 0
            refund_amount = float(payment.amount)
            if late:
                penalty = refund_amount * 0.20
                refund_amount -= penalty

            payment.status = "REFUNDED"
            payment.refund_amount = refund_amount
            payment.refund_id = f"MOCKREF-{payment.id}-{int(time.time())}"
            payment.save()

            refund_info = {"refunded": refund_amount, "penalty": penalty}

        booking.status = "CANCELLED"
        booking.save()

        # send cancellation email
        send_booking_cancelled_email(booking, refund_info.get("refunded"))

        # send cancellation email with debug
        try:
            print("📧 Sending cancellation email to:", booking.user.email)
            send_booking_cancelled_email(booking, refund_info.get("refunded"))
            print("✅ Cancel email sent")
        except Exception as e:
            print("❌ Cancel email error:", e)


# -------------------------
# Mock Payment (testing only)
# -------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mock_pay(request, pk):
    simulate = request.data.get('simulate', 'success')
    try:
        booking = Booking.objects.get(pk=pk, user=request.user)
    except Booking.DoesNotExist:
        return Response({"detail": "Booking not found."}, status=404)

    try:
        payment = booking.payment
    except Payment.DoesNotExist:
        return Response({"detail": "Payment not found."}, status=404)

    if simulate == 'success':
        payment.status = 'SUCCESS'
        payment.transaction_id = f"MOCKTXN-{payment.id}-{int(timezone.now().timestamp())}"
        payment.save()
        booking.status = 'CONFIRMED'
        booking.save()
        return Response({"detail": "Payment success, booking confirmed."})
    else:
        payment.status = 'FAILED'
        payment.save()
        booking.status = 'CANCELLED'
        booking.save()
        return Response({"detail": "Payment failed, booking cancelled."}, status=400)


# -------------------------
# Stripe Checkout
# -------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request, booking_id):
    try:
        booking = Booking.objects.get(pk=booking_id, user=request.user)
    except Booking.DoesNotExist:
        return JsonResponse({"detail": "Booking not found."}, status=404)

    if booking.status != 'PENDING':
        return JsonResponse({"detail": "Booking must be PENDING to pay."}, status=400)

    payment = booking.payment
    amount_in_paise = int(round(float(payment.amount) * 100))

    success_url = f"{DOMAIN}/my-bookings/?payment=success"
    cancel_url = f"{DOMAIN}/my-bookings/?payment=cancel"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': f'Booking #{booking.id} - {booking.vehicle}',
                    },
                    'unit_amount': amount_in_paise,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'booking_id': str(booking.id), 'payment_id': str(payment.id)}
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    payment.stripe_session_id = session.id
    payment.save(update_fields=['stripe_session_id'])

    return JsonResponse({'sessionId': session.id, 'publishableKey': STRIPE_PUBLISHABLE_KEY})


@csrf_exempt
@api_view(['POST'])
@permission_classes([])  # Stripe sends requests, not users
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        print(f"Webhook error: {e}")
        return HttpResponse(status=400)

    print(f"Stripe event received: {event['type']}")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        booking_id = session.get('metadata', {}).get('booking_id')
        payment_id = session.get('metadata', {}).get('payment_id')
        print(f"Metadata booking_id={booking_id}, payment_id={payment_id}")

        try:
            payment = Payment.objects.get(pk=payment_id)
            booking = payment.booking
            print(f"Payment and booking found: Payment ID {payment.id}, Booking ID {booking.id}")

            payment.status = 'SUCCESS'
            payment.transaction_id = session.get('payment_intent')
            payment.save()

            booking.status = 'CONFIRMED'
            booking.save()

            send_booking_confirmation_email(booking)
            print(f"Booking confirmed and email sent for booking ID {booking.id}")

        except Payment.DoesNotExist:
            print(f"Payment with ID {payment_id} does not exist")

    return HttpResponse(status=200)

# -------------------------
# Admin: list all bookings
# -------------------------
class AdminBookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Booking.objects.all().order_by('-created_at')
