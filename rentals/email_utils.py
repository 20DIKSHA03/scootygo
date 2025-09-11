# rentals/email_utils.py
from django.core.mail import send_mail
from django.conf import settings

def send_booking_confirmation_email(booking):
    subject = f"Booking Confirmed: {booking.vehicle.brand} {booking.vehicle.model_name}"
    message = (
        f"Hi {booking.user.username},\n\n"
        f"Your booking has been confirmed!\n\n"
        f"Vehicle: {booking.vehicle.brand} {booking.vehicle.model_name}\n"
        f"From: {booking.start_time}\n"
        f"To: {booking.end_time}\n"
        f"Total Price: ₹{booking.total_price}\n\n"
        "Thank you for using ScootyGo!"
    )
    recipient = [booking.user.email]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient)

def send_booking_cancelled_email(booking, refund_amount=None):
    subject = f"Booking Cancelled: {booking.vehicle.brand} {booking.vehicle.model_name}"
    message = (
        f"Hi {booking.user.username},\n\n"
        f"Your booking has been cancelled.\n"
    )
    if refund_amount is not None:
        message += f"Refund Amount: ₹{refund_amount}\n\n"
    message += "We hope to see you again soon!"
    recipient = [booking.user.email]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient)
