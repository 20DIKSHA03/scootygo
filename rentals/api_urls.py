from django.urls import path, include
from rest_framework import routers
from .api_views import (
    VehicleViewSet, BookingViewSet, RegisterView, ProfileView
)
from .views import (
    create_checkout_session, stripe_webhook
)

router = routers.DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicles')
router.register(r'bookings', BookingViewSet, basename='bookings')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
]
