from django.core.management.base import BaseCommand
from rentals.models import Booking, Payment, VehicleImage, Vehicle


class Command(BaseCommand):
    help = "Seed demo vehicles for ScootyGo project"

    def handle(self, *args, **kwargs):
        # Clean existing data
        self.stdout.write("Deleting old data…")
        Payment.objects.all().delete()
        Booking.objects.all().delete()
        VehicleImage.objects.all().delete()
        Vehicle.objects.all().delete()

        demo_vehicles = [
            {
                "vehicle_type": "scooty",
                "brand": "Honda",
                "model_name": "Activa 6G",
                "plate_number": "MH12AB1234",
                "description": "Reliable city scooter, fuel efficient.",
                "price_per_hour": 150.00,
                "price_per_day": 1600.00,
            },
            {
                "vehicle_type": "bike",
                "brand": "Royal Enfield",
                "model_name": "Bullet 350",
                "plate_number": "MH12XY6789",
                "description": "Classic motorcycle for enthusiasts.",
                "price_per_hour": 200.00,
                "price_per_day": 2000.00,
            },
        ]

        # Remote image URLs (from Unsplash/Bing)
        demo_vehicle_images = {
            "Activa 6G": [
                "https://tse1.mm.bing.net/th/id/OIP.C5Iz3eepZwm1m6aXAQ6tiAHaFj?r=0&rs=1&pid=ImgDetMain&o=7&rm=3"
            ],
            "Bullet 350": [
                "https://th.bing.com/th/id/R.bc1c24c7b8f9c634da99fc7da61fbe36?rik=VWxDjIxQSP9YWg&pid=ImgRaw&r=0"
            ],
        }

        for vdata in demo_vehicles:
            vehicle = Vehicle.objects.create(**vdata)
            self.stdout.write(self.style.SUCCESS(f"Created vehicle: {vehicle.brand} {vehicle.model_name}"))

            for url in demo_vehicle_images.get(vehicle.model_name, []):
                VehicleImage.objects.create(vehicle=vehicle, image=url)
                self.stdout.write(f" → Added image for {vehicle.model_name}: {url}")

        self.stdout.write(self.style.SUCCESS("✅ Demo vehicles seeded successfully!"))
