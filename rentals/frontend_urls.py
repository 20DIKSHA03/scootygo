from django.urls import path
from . import frontend_views

urlpatterns = [
    path('', frontend_views.home, name='home'),
    path('login/', frontend_views.login_view, name='login'),
    path('register/', frontend_views.register_view, name='register_page'),
    path('profile/', frontend_views.profile_view, name='profile'),
    path('my-bookings/', frontend_views.user_bookings_page, name='user_bookings'),
]
