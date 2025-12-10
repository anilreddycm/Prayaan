from rest_framework import serializers
from .models import Car


class CarSerializer(serializers.ModelSerializer):
    """Serializer for Car model - used in REST API endpoints"""
    
    class Meta:
        model = Car
        fields = [
            'id', 'category', 'ac_type', 'total_cars', 'registration_number',
            'image', 'price', 'price_per_hour', 'price_per_km',
            'fuel_consumption', 'status'
        ]
        read_only_fields = ['id']

    def validate_registration_number(self, value):
        """Ensure registration number is unique"""
        if value:
            # Exclude current instance if updating
            qs = Car.objects.filter(registration_number=value.upper())
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("A car with this registration number already exists.")
        return value.upper() if value else value

    def create(self, validated_data):
        """Create a new car"""
        return Car.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update an existing car"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
