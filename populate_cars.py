#!/usr/bin/env python
"""
Script to populate the database with sample cars for testing
Run with: python manage.py shell < populate_cars.py
Or: python manage.py shell
>>> exec(open('populate_cars.py').read())
"""

import os
from django.core.files.base import ContentFile
from app.models import Car
from PIL import Image
from io import BytesIO

def create_sample_image(name, color_hex):
    """Create a simple colored image for testing"""
    img = Image.new('RGB', (400, 300), color=color_hex)
    img_io = BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    return img_io

def populate_cars():
    """Add sample cars to the database"""
    
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
            'description': 'Classic luxury sedan'
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
            'description': 'Spacious SUV for family trips'
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
            'description': 'Budget-friendly van'
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
            'description': 'Comfortable sedan'
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
            'description': 'Premium luxury SUV'
        },
    ]
    
    for car_data in cars_data:
        # Check if car already exists
        if Car.objects.filter(registration_number=car_data['registration_number']).exists():
            print(f"⚠️ Car {car_data['registration_number']} already exists, skipping...")
            continue
        
        # Create image
        image_file = create_sample_image(car_data['category'], car_data.pop('color'))
        
        # Remove description if not in model
        car_data.pop('description', None)
        
        # Create car
        car = Car.objects.create(**car_data)
        
        # Save image
        filename = f"{car_data['registration_number']}.jpg"
        car.image.save(filename, ContentFile(image_file.read()), save=True)
        
        print(f"✅ Created car: {car.category} ({car.registration_number}) - ₹{car.price}/day")
    
    # Verify
    total = Car.objects.count()
    print(f"\n✅ Total cars in database: {total}")

if __name__ == '__main__':
    populate_cars()
