# app/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Booking, Customer, Driver


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['pickup_location', 'drop_location', 'start_datetime', 'expected_return_datetime', 'night_halt']
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "expected_return_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class EditProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = Customer
        fields = ['phone', 'address', 'aadhar_number', 'license_number', 'profile_pic']

    def save(self, commit=True):
        customer = super().save(commit=False)
        user = customer.user

        # Update User fields
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')

        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data.get('password'))

        if commit:
            user.save()
            customer.save()
        return customer


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = [
            'name', 'image', 'license_number', 'aadhar_number', 
            'phone', 'email', 'address', 'experience'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter driver full name'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter license number'
            }),
            'aadhar_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Aadhar number'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter address',
                'rows': 3
            }),
            'experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Years of experience'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = [
            'name', 'image', 'license_number', 'aadhar_number', 
            'phone', 'email', 'address', 'experience'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter driver full name'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter license number'
            }),
            'aadhar_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Aadhar number'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter address',
                'rows': 3
            }),
            'experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Years of experience'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }


# --- Car ModelForm added for app-level CRUD ---
class CarForm(forms.ModelForm):
    class Meta:
        from .models import Car
        model = Car
        fields = [
            'category', 'ac_type', 'total_cars', 'registration_number',
            'image', 'price', 'price_per_hour', 'price_per_km',
            'fuel_consumption', 'status'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'ac_type': forms.Select(attrs={'class': 'form-control'}),
            'total_cars': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control-file'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_per_hour': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_per_km': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fuel_consumption': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_registration_number(self):
        reg = self.cleaned_data.get('registration_number')
        if reg:
            return reg.upper()
        return reg

    def save(self, commit=True):
        car = super().save(commit=False)
        # Additional normalization or defaulting can go here
        if commit:
            car.save()
        return car

