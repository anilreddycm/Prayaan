# views.py - Main authentication and booking views
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q, Sum
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from decimal import Decimal

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

import requests
import logging

from .forms import BookingForm, EditProfileForm, CarForm
from .models import Car, Booking, Customer, Driver, Maintenance
from .serializers import CarSerializer


# Set up logging
logger = logging.getLogger(__name__)


# ==================== MAIN PAGE VIEWS ====================

def index(request):
    return render(request, 'app/index.html')


def cars(request):
    query = request.GET.get('q', '')
    if query:
        cars = Car.objects.filter(
            Q(category__icontains=query) |
            Q(ac_type__icontains=query) |
            Q(fuel_consumption__icontains=query)
        )
    else:
        cars = Car.objects.all()
    return render(request, 'app/cars.html', {'cars': cars, 'query': query})


def about(request):
    return render(request, 'app/about.html')


# ==================== BOOKING VIEWS ====================

@login_required
def booking_view(request):
    car_id = request.GET.get("car_id") or request.POST.get("car_id")
    car = get_object_or_404(Car, id=car_id)
    customer, created = Customer.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.car = car
            booking.customer = request.user

            # Dynamic calculation
            km_to_destination = float(request.POST.get("km_to_destination", 0))
            hours_used = max(int(request.POST.get("hours_used", 4)), 4)
            drive_type = request.POST.get("drive_type")

            # Handle self-drive Aadhaar & License
            if drive_type == "self_drive":
                aadhaar_number = request.POST.get("aadhaar_number")
                license_number = request.POST.get("license_number")
                if not aadhaar_number or not license_number:
                    messages.error(request, "Aadhaar and License required for self-drive.")
                    return render(request, "app/booking.html", {"form": form, "car": car, "customer": customer})

                customer.aadhar_number = aadhaar_number
                customer.license_number = license_number
                customer.save()

            # Calculate total, advance, pending
            per_hour_charge = car.price_per_hour
            per_km_charge = car.price_per_km
            hourly_amount = per_hour_charge * hours_used
            km_amount = per_km_charge * km_to_destination
            total_amount = max(hourly_amount, km_amount, per_hour_charge * 4)

            if drive_type == "with_driver":
                total_amount += 500

            advance_payment = total_amount * 0.2
            pending_payment = total_amount - advance_payment

            # Save booking
            booking.kms_to_destination = km_to_destination
            booking.hours_used = hours_used
            booking.total_amount = total_amount
            booking.advance_payment = advance_payment
            booking.pending_payment = pending_payment
            booking.drive_type = drive_type
            booking.start_km_reading = 0
            booking.save()

            # Reduce car stock
            car.total_cars -= 1
            car.save()

            messages.success(request, f"Booking successful! Pending Amount: ₹{pending_payment:.2f}")
            return redirect("booked_cars")

    else:
        form = BookingForm()

    return render(request, "app/booking.html", {"form": form, "car": car, "customer": customer})


# ==================== AUTHENTICATION VIEWS ====================

def register_view(request):
    # Allow viewing register page even if authenticated (show appropriate message)
    # Only prevent registration if already authenticated
    
    if request.method == 'POST':
        # Only allow POST (actual registration) if not authenticated
        if request.user.is_authenticated:
            messages.warning(request, "You are already registered and logged in. Please logout to create a new account.")
            return redirect('index')
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()
        profile_pic = request.FILES.get('profile_pic')

        # Validation
        if not username or not email or not password1 or not password2:
            messages.error(request, "All fields are required.")
            return render(request, 'app/register.html')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'app/register.html')

        if len(password1) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'app/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return render(request, 'app/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered. Please login or use another email.")
            return render(request, 'app/register.html')

        try:
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password1)

            # Safely create Customer
            Customer.objects.get_or_create(user=user, defaults={'profile_pic': profile_pic})

            login(request, user)
            messages.success(request, f"Registration successful! Welcome, {username}!")
            logger.info(f"New user registered: {username}")
            return redirect('index')
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            logger.error(f"Registration error for {username}: {str(e)}")
            return render(request, 'app/register.html')

    return render(request, 'app/register.html')


def login_view(request):
    if request.user.is_authenticated:
        # If user tries to visit /login while already logged in,
        # show them the login page anyway (don't auto-redirect)
        pass

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'app/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            logger.info(f"User {username} logged in successfully")
            return redirect('index')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            logger.warning(f"Failed login attempt for username: {username}")

    return render(request, 'app/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    """User profile view"""
    if request.method == 'POST':
        # Update user profile
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        
        # Basic validation
        if user.first_name and user.email:
            try:
                user.save()
                messages.success(request, 'Profile updated successfully!')
            except Exception as e:
                messages.error(request, 'Error updating profile. Please try again.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return render(request, 'app/profile.html')


# ==================== DISTANCE CALCULATOR VIEWS ====================

def distance_calculator(request):
    """Render the distance calculator template with API key"""
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
    
    if not api_key:
        logger.error("Google Maps API key not found in settings")
    else:
        logger.info(f"API key found: {api_key[:10]}...")
    
    return render(request, 'app/distance_calculator.html', {
        'google_maps_api_key': api_key
    })


def calculate_distance(request):
    """Calculate distance between two points using Google Maps API via AJAX"""
    if request.method == 'POST':
        origin = request.POST.get('origin')
        destination = request.POST.get('destination')
        
        logger.info(f"Distance calculation request: {origin} -> {destination}")
        
        if not origin or not destination:
            logger.error("Missing origin or destination")
            return JsonResponse({'error': 'Both origin and destination are required'})
        
        api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        if not api_key:
            logger.error("Google Maps API key not configured")
            return JsonResponse({'error': 'Google Maps API key not configured. Please check your settings.'})
        
        url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
        
        params = {
            'origins': origin,
            'destinations': destination,
            'units': 'metric',
            'key': api_key
        }
        
        logger.info(f"Making API request to: {url}")
        logger.info(f"Request params: origins={origin}, destinations={destination}, units=metric")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            logger.info(f"API Response status code: {response.status_code}")
            
            response_text = response.text
            logger.info(f"API Response: {response_text}")
            
            if response.status_code != 200:
                logger.error(f"HTTP Error: {response.status_code}")
                return JsonResponse({'error': f'HTTP Error: {response.status_code}'})
            
            data = response.json()
            
            if data['status'] == 'OK':
                element = data['rows'][0]['elements'][0]
                logger.info(f"Element status: {element['status']}")
                
                if element['status'] == 'OK':
                    distance = element['distance']['text']
                    duration = element['duration']['text']
                    distance_value = element['distance']['value']
                    duration_value = element['duration']['value']
                    
                    fare_per_km = 12.50
                    fare_per_hour = 200
                    
                    distance_km = distance_value / 1000
                    duration_hours = duration_value / 3600
                    
                    distance_fare = distance_km * fare_per_km
                    time_fare = duration_hours * fare_per_hour
                    estimated_fare = max(distance_fare, time_fare)
                    
                    logger.info(f"Calculation successful: {distance}, {duration}")
                    
                    return JsonResponse({
                        'success': True,
                        'distance': distance,
                        'duration': duration,
                        'distance_km': round(distance_km, 2),
                        'duration_hours': round(duration_hours, 1),
                        'distance_fare': round(distance_fare, 2),
                        'time_fare': round(time_fare, 2),
                        'estimated_fare': round(estimated_fare, 2),
                        'origin': origin,
                        'destination': destination
                    })
                else:
                    error_msg = f"Route calculation failed: {element['status']}"
                    if element['status'] == 'NOT_FOUND':
                        error_msg = "One or both locations could not be found. Please check your addresses."
                    elif element['status'] == 'ZERO_RESULTS':
                        error_msg = "No route could be found between these locations."
                    
                    logger.error(f"Element error: {element['status']}")
                    return JsonResponse({'error': error_msg})
            else:
                error_msg = f"API Error: {data['status']}"
                if data['status'] == 'REQUEST_DENIED':
                    error_msg = "API request denied. Please check your API key and billing settings."
                elif data['status'] == 'INVALID_REQUEST':
                    error_msg = "Invalid request. Please check your input locations."
                elif data['status'] == 'OVER_QUERY_LIMIT':
                    error_msg = "API quota exceeded. Please try again later."
                elif data['status'] == 'UNKNOWN_ERROR':
                    error_msg = "Unknown API error. Please try again."
                
                logger.error(f"API Status error: {data['status']}")
                if 'error_message' in data:
                    logger.error(f"API Error message: {data['error_message']}")
                    error_msg += f" Details: {data['error_message']}"
                
                return JsonResponse({'error': error_msg})
                
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return JsonResponse({'error': 'Request timeout. Please try again.'})
        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
            return JsonResponse({'error': 'Connection error. Please check your internet connection.'})
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {str(e)}")
            return JsonResponse({'error': f'Request error: {str(e)}'})
        except ValueError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return JsonResponse({'error': 'Invalid response from Google API'})
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({'error': f'Unexpected error: {str(e)}'})
    
    return JsonResponse({'error': 'Invalid request method'})


# ==================== BOOKING STATUS VIEWS ====================

@login_required
def booked_cars_view(request):
    if request.user.is_staff:
        total_cars_booked = Booking.objects.filter(is_returned=False).count()
        r_total_cars_booked = Booking.objects.filter(is_returned=True).count()
        bookings = Booking.objects.filter(is_returned=False)
    else:
        total_cars_booked = Booking.objects.filter(customer=request.user, is_returned=False).count()
        r_total_cars_booked = Booking.objects.filter(is_returned=True).count()
        bookings = Booking.objects.filter(customer=request.user)

    context = {
        'bookings': bookings,
        'total_cars_booked': total_cars_booked,
        "r_total_cars_booked": r_total_cars_booked,
        'now': timezone.now(),
    }
    return render(request, 'app/booked_cars.html', context)


@login_required
def return_cars_view(request):
    """
    View for displaying returned cars.
    - Staff sees all returned cars
    - Customers see only their returned cars
    """
    if request.user.is_staff:
        # Staff sees all returned cars
        bookings = Booking.objects.filter(is_returned=True).order_by('-returned_at')
        returned_cars = bookings.count()
        is_staff_view = True
    else:
        # Customers see only their own returned cars
        bookings = Booking.objects.filter(customer=request.user, is_returned=True).order_by('-returned_at')
        returned_cars = bookings.count()
        is_staff_view = False

    context = {
        'bookings': bookings,
        'returned_cars': returned_cars,
        'is_staff_view': is_staff_view,
    }
    return render(request, 'app/return_cars.html', context)


@login_required
def returns_list_view(request):
    bookings = Booking.objects.filter(customer=request.user, is_returned=True).order_by('-returned_at')
    return render(request, "app/customer_returned_cars.html", {"bookings": bookings})


@login_required
def cancel_booking_view(request, booking_id):
    """
    Cancel a booking - only before the booking start date.
    Customers can only cancel their own bookings.
    Staff can cancel any booking.
    """
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Permission check: Customer can only cancel their own bookings
    if not request.user.is_staff and booking.customer != request.user:
        messages.error(request, "You don't have permission to cancel this booking.")
        return redirect('booked_cars')
    
    # Check if booking can be cancelled (only if not started yet)
    if booking.start_datetime <= timezone.now():
        messages.error(request, "Cannot cancel a booking that has already started.")
        return redirect('booked_cars')
    
    # Check if already returned
    if booking.is_returned:
        messages.error(request, "Cannot cancel a booking that has already been returned.")
        return redirect('return_cars')
    
    if request.method == "POST":
        reason = request.POST.get("cancellation_reason", "No reason provided")
        
        # Refund logic: Refund 80% of advance payment (20% cancellation fee)
        refund_amount = booking.advance_payment * Decimal('0.8') if booking.advance_payment else Decimal('0.00')
        
        # Store cancellation info
        booking.is_returned = True  # Mark as cancelled/returned
        booking.returned_at = timezone.now()
        booking.pending_payment = Decimal('0.00')  # No pending payment after cancellation
        booking.damage_reported = False
        booking.damage_fee = Decimal('0.00')
        
        # Add note to total_amount to track refund
        booking.total_amount = refund_amount
        
        # Increment car availability
        car = booking.car
        car.total_cars = (car.total_cars or 0) + 1
        car.save()
        
        booking.save()
        
        messages.success(
            request,
            f"Booking cancelled successfully! Refund of ₹{refund_amount:.2f} will be processed (80% of advance payment, 20% cancellation fee applied)."
        )
        return redirect('booked_cars')
    
    # GET request: Show cancellation confirmation page
    refund_amount = booking.advance_payment * Decimal('0.8') if booking.advance_payment else Decimal('0.00')
    cancellation_fee = booking.advance_payment - refund_amount if booking.advance_payment else Decimal('0.00')
    
    context = {
        'booking': booking,
        'refund_amount': refund_amount,
        'cancellation_fee': cancellation_fee,
    }
    return render(request, 'app/cancel_booking.html', context)


# ==================== DRIVER VIEWS ====================

@staff_member_required
def drivers_view(request):
    drivers = Driver.objects.all()
    total_drivers = Driver.objects.all().count()
    return render(request, "app/drivers.html", {"drivers": drivers, "total_drivers": total_drivers})


# ==================== CAR CRUD VIEWS ====================

@login_required
def car_list_view(request):
    cars_qs = Car.objects.all().order_by('category', 'registration_number')
    return render(request, 'app/car_list.html', {'cars': cars_qs})


@login_required
def car_detail_view(request, pk):
    car = get_object_or_404(Car, id=pk)
    return render(request, 'app/car_detail.html', {'car': car})


@staff_member_required
def car_create_view(request):
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save()
            messages.success(request, 'Car added successfully.')
            return redirect('car_detail', pk=car.id)
    else:
        form = CarForm()
    return render(request, 'app/car_form.html', {'form': form, 'title': 'Add Car'})


@staff_member_required
def car_update_view(request, pk):
    car = get_object_or_404(Car, id=pk)
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, 'Car updated successfully.')
            return redirect('car_detail', pk=car.id)
    else:
        form = CarForm(instance=car)
    return render(request, 'app/car_form.html', {'form': form, 'title': 'Edit Car'})


@staff_member_required
def car_delete_view(request, pk):
    car = get_object_or_404(Car, id=pk)
    if request.method == 'POST':
        car.delete()
        messages.success(request, 'Car deleted successfully.')
        return redirect('car_list')
    return render(request, 'app/car_confirm_delete.html', {'car': car})


# ==================== STAFF VIEWS ====================

@staff_member_required
def staff_booked_cars_view(request):
    bookings = Booking.objects.filter(is_returned=False).order_by('-start_datetime')
    total_cars_booked = Booking.objects.filter(is_returned=False).count()
    r_total_cars_booked = Booking.objects.filter(is_returned=True).count()

    return render(
        request,
        "app/staff_booked_cars.html",
        {
            "bookings": bookings,
            "total_cars_booked": total_cars_booked,
            "r_total_cars_booked": r_total_cars_booked,
        },
    )


@staff_member_required
def staff_returned_cars_list_view(request):
    bookings = Booking.objects.filter(is_returned=True).order_by('-returned_at')
    return render(request, 'app/staff_returned_cars_list.html', {'bookings': bookings})


@user_passes_test(lambda u: u.is_staff)
def staff_returned_cars_mark(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == "POST":
        # Check if damage was reported
        damage_reported = request.POST.get("damage_reported")
        booking.damage_reported = bool(damage_reported)
        
        damage_fee = request.POST.get("damage_fee")
        if damage_fee and booking.damage_reported:
            booking.damage_fee = Decimal(damage_fee)
            booking.pending_payment += Decimal(damage_fee)

        if not booking.is_returned:
            car = booking.car
            car.total_cars = (car.total_cars or 0) + 1
            car.save()

            booking.is_returned = True
            booking.returned_at = timezone.now()
            booking.total_amount = (booking.total_amount or Decimal('0.00')) + (booking.damage_fee or Decimal('0.00'))
            booking.pending_payment = (booking.total_amount or Decimal('0.00')) - (booking.advance_payment or Decimal('0.00'))

        booking.save()
    
    return redirect('staff_returned_cars_list')


@staff_member_required
def staff_returned_cars_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.is_returned:
        messages.info(request, f"The booking for {booking.car.category} is already returned.")
        return redirect("staff_booked_cars")

    booking.is_returned = True
    booking.returned_at = timezone.now()

    car = booking.car
    car.total_cars = (car.total_cars or 0) + 1
    car.save()

    if booking.damage_reported and booking.damage_fee:
        booking.total_amount = (booking.total_amount or Decimal('0.00')) + booking.damage_fee
    booking.pending_payment = (booking.total_amount or Decimal('0.00')) - (booking.advance_payment or Decimal('0.00'))

    booking.save()
    return redirect("staff_booked_cars")


# ==================== ADMIN DASHBOARD VIEW ====================

@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('index')
    
    total_bookings = Booking.objects.count()
    total_revenue = Booking.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_drivers = Driver.objects.count()
    total_cars = Car.objects.count()
    returned_cars = Booking.objects.filter(is_returned=True).count()
    pending_bookings = Booking.objects.filter(is_returned=False).count()
    
    context = {
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'total_drivers': total_drivers,
        'total_cars': total_cars,
        'returned_cars': returned_cars,
        'pending_bookings': pending_bookings,
    }
    return render(request, 'app/admin_dashboard.html', context)


# ==================== REST API - CAR CRUD ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def car_api_list(request):
    """
    GET: List all cars (authenticated users)
    POST: Create a new car (staff only)
    """
    if request.method == 'GET':
        cars = Car.objects.all()
        serializer = CarSerializer(cars, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff members can create cars.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = CarSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def car_api_detail(request, pk):
    """
    GET: Retrieve a specific car
    PUT: Update a car (staff only)
    DELETE: Delete a car (staff only)
    """
    try:
        car = Car.objects.get(pk=pk)
    except Car.DoesNotExist:
        return Response(
            {'error': 'Car not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = CarSerializer(car)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff members can update cars.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = CarSerializer(car, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff members can delete cars.'},
                status=status.HTTP_403_FORBIDDEN
            )
        car.delete()
        return Response(
            {'message': 'Car deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )
