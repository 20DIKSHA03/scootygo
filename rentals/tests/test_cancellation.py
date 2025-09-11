from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from ..models import Vehicle, Booking, Payment

User = get_user_model()

class CancellationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='u1', password='pass', email='u1@example.com')
        self.user2 = User.objects.create_user(username='u2', password='pass', email='u2@example.com')

        self.vehicle = Vehicle.objects.create(
            vehicle_type='scooty',
            brand='Honda',
            model_name='Activa',
            price_per_hour=50,
            price_per_day=400,
            is_active=True
        )
        self.start = timezone.now() + timezone.timedelta(days=2)
        self.end = self.start + timezone.timedelta(hours=4)

        self.booking = Booking.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            start_time=self.start,
            end_time=self.end,
            total_price=Decimal('200.00'),
            status='PENDING'
        )
        self.payment = Payment.objects.create(
            booking=self.booking,
            amount=self.booking.total_price,
            provider='mock',
            status='SUCCESS'
        )

        # Login user1 to get JWT token
        login_resp = self.client.post('/api/token/', {'username': 'u1', 'password': 'pass'}, format='json')
        token = login_resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

        self.client2 = APIClient()
        login_resp2 = self.client2.post('/api/token/', {'username': 'u2', 'password': 'pass'}, format='json')
        token2 = login_resp2.data['access']
        self.client2.credentials(HTTP_AUTHORIZATION='Bearer ' + token2)

    def test_cancel_by_owner_success(self):
        resp = self.client.post(reverse('bookings-detail', kwargs={'pk': self.booking.id}) + 'cancel/')
        self.assertEqual(resp.status_code, 200)
        self.booking.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.booking.status, 'CANCELLED')
        self.assertEqual(self.payment.status, 'REFUNDED')

    def test_cancel_by_other_user_forbidden(self):
        resp = self.client2.post(reverse('bookings-detail', kwargs={'pk': self.booking.id}) + 'cancel/')
        self.assertEqual(resp.status_code, 403)

    def test_double_cancel_is_idempotent(self):
        r1 = self.client.post(reverse('bookings-detail', kwargs={'pk': self.booking.id}) + 'cancel/')
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.post(reverse('bookings-detail', kwargs={'pk': self.booking.id}) + 'cancel/')
        self.assertEqual(r2.status_code, 400)
        self.booking.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'REFUNDED')

    def test_late_cancel_penalty_applies(self):
        self.booking.start_time = timezone.now() + timezone.timedelta(hours=10)
        self.booking.save()
        resp = self.client.post(reverse('bookings-detail', kwargs={'pk': self.booking.id}) + 'cancel/')
        self.assertEqual(resp.status_code, 200)
        j = resp.json()
        self.assertTrue(j.get('late_cancel', False))
        self.assertIn('refund', j)
