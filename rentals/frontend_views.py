# rentals/frontend_views.py
from django.shortcuts import render

def index(request):
    """Homepage → show vehicles list"""
    return render(request, "vehicles_list.html")

def vehicles_page(request):
    """Vehicles page"""
    return render(request, "vehicles_list.html")

def login_page(request):
    """Login form"""
    return render(request, "auth_login.html")

def register_page(request):
    """Register form"""
    return render(request, "auth_register.html")

def profile_page(request):
    """User profile page"""
    return render(request, "profile.html")

def user_bookings_page(request):
    """My bookings (frontend)"""
    return render(request, "user_bookings.html")

def bookings_page(request):
    """Admin/user bookings list"""
    return render(request, "bookings_list.html")
