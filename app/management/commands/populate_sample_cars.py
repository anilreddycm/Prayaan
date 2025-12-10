"""
Django management command to populate the database with sample cars
Run with: python manage.py populate_sample_cars
"""

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from app.models import Car
from PIL import Image
from io import BytesIO

class Command(BaseCommand):
    help = 'Populate the database with sample cars for testing'

    def create_sample_image(self, name, color_hex):
        """Create a simple colored image for testing"""
        img = Image.new('RGB', (400, 300), color=color_hex)
        img_io = BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        return img_io

    def handle(self, *args, **options):
        """Main command handler"""
        
        cars_data = [
            {
                'category': 'Ambassador',
                'ac_type': 'AC',
                'fuel_consumption': 'petrol',
                'registration_number': 'DL01AB0001',
                'price': 2000.00,
                'price_per_hour': 250,
                'price_per_km': 15,
                'total_cars': 3,
                'color': '#FF6B6B',
            },
            {
                'category': 'Tata Sumo',
                'ac_type': 'AC',
                'fuel_consumption': 'diesel',
                'registration_number': 'DL01AB0002',
                'price': 2500.00,
                'price_per_hour': 300,
                'price_per_km': 18,
                'total_cars': 2,
                'color': '#4ECDC4',
            },
            {
                'category': 'Maruti Omni',
                'ac_type': 'Non-AC',
                'fuel_consumption': 'petrol',
                'registration_number': 'DL01AB0003',
                'price': 1500.00,
                'price_per_hour': 200,
                'price_per_km': 12,
                'total_cars': 5,
                'color': '#95E1D3',
            },
            {
                'category': 'Maruti Esteem',
                'ac_type': 'AC',
                'fuel_consumption': 'petrol',
                'registration_number': 'DL01AB0004',
                'price': 1800.00,
                'price_per_hour': 225,
                'price_per_km': 14,
                'total_cars': 4,
                'color': '#F38181',
            },
            {
                'category': 'Mahindra Armada',
                'ac_type': 'AC',
                'fuel_consumption': 'diesel',
                'registration_number': 'DL01AB0005',
                'price': 3500.00,
                'price_per_hour': 400,
                'price_per_km': 22,
                'total_cars': 2,
                'color': '#AA96DA',
            },
        ]
        
        created_count = 0
        skipped_count = 0
        
        for car_data in cars_data:
            # Check if car already exists
            if Car.objects.filter(registration_number=car_data['registration_number']).exists():
                self.stdout.write(self.style.WARNING(f"⚠️  Car {car_data['registration_number']} already exists, skipping..."))
                skipped_count += 1
                continue
            
            # Create image
            color = car_data.pop('color')
            image_file = self.create_sample_image(car_data['category'], color)
            
            # Create car
            car = Car.objects.create(**car_data)
            
            # Save image
            filename = f"{car_data['registration_number']}.jpg"
            car.image.save(filename, ContentFile(image_file.read()), save=True)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created car: {car.category} ({car.registration_number}) - ₹{car.price}/day"))
            created_count += 1
        
        # Summary
        total = Car.objects.count()
        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS(f"✅ Total cars in database: {total}"))
        self.stdout.write(self.style.SUCCESS(f"✅ New cars created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"⚠️  Cars skipped (already existed): {skipped_count}"))
        self.stdout.write(self.style.SUCCESS(f"{'='*60}\n"))
