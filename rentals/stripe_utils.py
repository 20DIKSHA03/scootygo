import stripe
import environ
from pathlib import Path

# -------------------------------------------------------------------
# Load environment variables from project root (.env next to manage.py)
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # project root (where manage.py is)
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# -------------------------------------------------------------------
# Stripe configuration
# -------------------------------------------------------------------
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
DOMAIN = env("DOMAIN", default="http://localhost:8000")

# Initialize Stripe with secret key
stripe.api_key = STRIPE_SECRET_KEY

# -------------------------------------------------------------------
# Helper: create checkout session
# -------------------------------------------------------------------
def create_checkout_session(booking, success_url=None, cancel_url=None):
    if not success_url:
        success_url = f"{DOMAIN}/my-bookings/?session_id={{CHECKOUT_SESSION_ID}}"
    if not cancel_url:
        cancel_url = f"{DOMAIN}/my-bookings/"

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "inr",
                "product_data": {
                    "name": f"{booking.vehicle.brand} {booking.vehicle.model_name}",
                },
                "unit_amount": int(float(booking.total_price) * 100),  # convert to paise
            },
            "quantity": 1,
        }],
        mode="payment",
        customer_email=booking.user.email,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"booking_id": str(booking.id), "user_id": str(booking.user.id)},
    )
    return session

# -------------------------------------------------------------------
# Helper: verify and retrieve Stripe event (webhook)
# -------------------------------------------------------------------
def retrieve_event(payload, sig_header):
    event = stripe.Webhook.construct_event(
        payload, sig_header, STRIPE_WEBHOOK_SECRET
    )
    return event
