// rentals/static/js/stripe_payment.js

// Initialize Stripe with your publishable key
const stripe = Stripe('pk_test_51S5WelCs0MpeonbBSe6xYYyOsfSxQVSJD6lShtluyb77UUQya5CyDbklTHr9VJIVZetIOuJ1Z7lLqF7ygw6mnA4i001XF6iiox');  // Replace with your Stripe publishable key

// Create Stripe elements and card instance
const elements = stripe.elements();
const card = elements.create('card');
card.mount('#card-element');

let currentBookingId = null;

async function startStripePayment(bookingId) {
  currentBookingId = bookingId;

  // Call backend to create payment intent
  const response = await fetch(`/api/payments/stripe/create/${bookingId}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('sg_access')}`,
    },
    body: JSON.stringify({ currency: 'inr' }),
  });

  const data = await response.json();

  if (!response.ok || !data.client_secret) {
    alert('Failed to initiate payment: ' + (data.detail || JSON.stringify(data)));
    return;
  }

  // Confirm card payment
  const result = await stripe.confirmCardPayment(data.client_secret, {
    payment_method: {
      card: card,
      billing_details: {
        name: 'Customer Name', // Change if you can supply actual user name
      },
    },
  });

  if (result.error) {
    alert('Payment failed: ' + result.error.message);
  } else if (result.paymentIntent && result.paymentIntent.status === 'succeeded') {
    alert('Payment successful! Booking confirmed.');
    // Refresh the bookings list or update UI accordingly
    if (typeof loadBookings === 'function') {
      loadBookings(); // call global loadBookings if available
    }
  }
}

// Attach click event delegation for pay buttons (since buttons generated dynamically)
document.addEventListener('click', function(event) {
  if(event.target && event.target.id === 'pay-button') {
    const bookingId = event.target.getAttribute('data-booking-id');
    if(bookingId) {
      startStripePayment(parseInt(bookingId));
    }
  }
}, false);
