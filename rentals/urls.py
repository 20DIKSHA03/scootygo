from django.urls import path, include
from rest_framework import routers
from .views import (
    VehicleViewSet, BookingViewSet, RegisterView, ProfileView,
    mock_pay, AdminBookingListView,
    create_checkout_session, stripe_webhook
)
from . import frontend_views

router = routers.DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicles')
router.register(r'bookings', BookingViewSet, basename='bookings')

urlpatterns = [
    # ====================
    # API ROUTES
    # ====================
    path('api/', include(router.urls)),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/profile/', ProfileView.as_view(), name='profile'),
    path('api/payments/mock/<int:pk>/', mock_pay, name='mock-pay'),
    path('api/admin/bookings/', AdminBookingListView.as_view(), name='admin-bookings'),
    path('api/payments/create-checkout-session/<int:booking_id>/', create_checkout_session, name='create-checkout-session'),
    path('api/payments/webhook/', stripe_webhook, name='stripe-webhook'),

    # ====================
    # FRONTEND ROUTES
    # ====================
    path('', frontend_views.index, name='home'),
    path('vehicles/', frontend_views.vehicles_page, name='vehicles_page'),
    path('login/', frontend_views.login_page, name='login'),
    path('register/', frontend_views.register_page, name='register'),
    path('profile/', frontend_views.profile_page, name='profile_page'),
    path('my-bookings/', frontend_views.user_bookings_page, name='user_bookings'),
    path('bookings/', frontend_views.bookings_page, name='bookings_page'),
]
