from django.contrib import admin
from django.utils.html import format_html
from .models import Car, Booking, Maintenance, Driver, Customer


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'category', 'registration_number', 'ac_type', 'total_cars', 'price', 'status']
    list_filter = ['ac_type', 'status', 'fuel_consumption', 'category']
    search_fields = ['category', 'registration_number']
    readonly_fields = ['image_preview_large']
    ordering = ['category', 'registration_number']
    actions = ['mark_available', 'mark_in_repair']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'ac_type', 'registration_number', 'fuel_consumption')
        }),
        ('Pricing', {
            'fields': ('price', 'price_per_hour', 'price_per_km')
        }),
        ('Inventory', {
            'fields': ('total_cars', 'status')
        }),
        ('Media', {
            'fields': ('image', 'image_preview_large'),
            'description': 'Upload car image (JPG, PNG recommended). Images are displayed on frontend.'
        }),
        ('Return Information', {
            'fields': ('is_returned', 'returned_at', 'pending_payment', 'damage_reported', 'damage_fee'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        """Small thumbnail in list view"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Image"

    def image_preview_large(self, obj):
        """Large preview in edit form"""
        if obj.image:
            return format_html(
                '<img src="{}" max-width="300px" style="max-height: 300px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No image uploaded"
    image_preview_large.short_description = "Current Image Preview"

    def mark_available(self, request, queryset):
        """Admin action: Mark cars as available"""
        updated = queryset.update(status='available')
        self.message_user(request, f'{updated} car(s) marked as available.')
    mark_available.short_description = "Mark selected cars as available"

    def mark_in_repair(self, request, queryset):
        """Admin action: Mark cars as in repair"""
        updated = queryset.update(status='repair')
        self.message_user(request, f'{updated} car(s) marked as in repair.')
    mark_in_repair.short_description = "Mark selected cars as in repair"


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'license_number', 'aadhar_number', 'status', 'experience']
    list_filter = ['status', 'experience']
    search_fields = ['name', 'phone', 'license_number', 'aadhar_number']
    readonly_fields = ['created_at'] if hasattr(Driver, 'created_at') else []


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'aadhar_number', 'license_number']
    search_fields = ['user__username', 'phone', 'aadhar_number']
    readonly_fields = ['user']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'car', 'start_datetime', 'is_returned', 'total_amount', 'pending_payment']
    list_filter = ['is_returned', 'start_datetime', 'drive_type']
    search_fields = ['customer__username', 'car__category']
    readonly_fields = ['created_at', 'returned_at']
    fieldsets = (
        ('Booking Details', {
            'fields': ('customer', 'car', 'drive_type')
        }),
        ('DateTime', {
            'fields': ('start_datetime', 'expected_return_datetime', 'actual_return_datetime', 'returned_at', 'created_at')
        }),
        ('Location & Distance', {
            'fields': ('pickup_location', 'drop_location', 'distance_km', 'kms_to_destination', 'hours_used')
        }),
        ('Payment', {
            'fields': ('total_amount', 'advance_payment', 'pending_payment')
        }),
        ('KM Reading', {
            'fields': ('start_km_reading', 'end_km_reading')
        }),
        ('Damage & Return', {
            'fields': ('damage_reported', 'damage_fee', 'is_returned')
        }),
        ('Other', {
            'fields': ('night_halt',)
        }),
    )


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ['car', 'date', 'cost']
    list_filter = ['date', 'car']
    search_fields = ['car__category', 'car__registration_number']
    readonly_fields = ['created_at'] if hasattr(Maintenance, 'created_at') else []

