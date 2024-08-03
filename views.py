from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
import requests
from datetime import datetime
import json
from .models import UserProfile, Flight
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Temperature conversion function
def temp_celsius(k):
    return round(k - 273.15, 2)

# Time formatting function
def time_format(t):
    return datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')

# Function to register a new user
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        email = request.POST['email']
        is_staff = request.POST.get('is_staff', False)
        city = request.POST['city'] if is_staff else None

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'register.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return render(request, 'register.html')

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return render(request, 'register.html')

        user = User.objects.create_user(username=username, password=password1, email=email)
        user_profile = UserProfile(user=user, is_staff=is_staff, city=city, email=email)
        user_profile.save()

        messages.success(request, "User registered successfully")
        return redirect('login')
    else:
        return render(request, 'register.html')

# Function to log in a user
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not hasattr(user, 'userprofile'):
                UserProfile.objects.create(user=user, email=user.email)
                messages.info(request, 'User profile created successfully.')
            if user.userprofile.is_staff:
                return redirect('staff_dashboard')
            else:
                return redirect('pilot_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

# Function to log out a user
def logout_view(request):
    logout(request)
    return redirect('login')

# Home view with weather and forecast data
@login_required
def home(request):
    weather_data = None
    forecast_data = None
    alerts = None
    error_message = None

    if request.method == 'POST':
        city = request.POST['city']
        api_key = '2a12086c7431fc7c4a964dc3aa4bb27b'
        current_weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}"
        response = requests.get(current_weather_url)
        data = response.json()

        if data['cod'] == 200:
            weather_data = {
                'city': data['name'],
                'temperature': temp_celsius(data['main']['temp']),
                'feels_like': temp_celsius(data['main']['feels_like']),
                'temp_min': temp_celsius(data['main']['temp_min']),
                'temp_max': temp_celsius(data['main']['temp_max']),
                'pressure': data['main']['pressure'],
                'humidity': data['main']['humidity'],
                'visibility': data.get('visibility', 0),
                'wind_speed': data['wind']['speed'],
                'wind_deg': data['wind']['deg'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'country': data['sys']['country'],
                'sunrise': time_format(data['sys']['sunrise']),
                'sunset': time_format(data['sys']['sunset']),
            }

            forecast_response = requests.get(forecast_url)
            forecast_data = forecast_response.json()['list'][:5]
            for forecast in forecast_data:
                forecast['main']['temp'] = temp_celsius(forecast['main']['temp'])
                forecast['dt_txt'] = time_format(forecast['dt'])

            alerts = forecast_response.json().get('alerts', [])
            for alert in alerts:
                alert['start'] = time_format(alert['start'])
                alert['end'] = time_format(alert['end'])

        else:
            error_message = data.get('message', 'Invalid city')

    return render(request, 'i6.html', {
        'weather_data': weather_data,
        'forecast_data': forecast_data,
        'alerts': alerts,
        'error_message': error_message
    })

# Dashboard view
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

# About Us view
@login_required
def about_us(request):
    return render(request, 'about_us.html')

# Staff dashboard view
@login_required
def staff_dashboard(request):
    if request.user.userprofile.is_staff:
        city = request.user.userprofile.city
        flights = Flight.objects.filter(
            Q(departure_location=city) | Q(arrival_location=city) | Q(status="Diverted")
        )
        return render(request, 'staff_dashboard.html', {'flights': flights})
    return HttpResponse("Unauthorized", status=401)

# Pilot dashboard view
@login_required
def pilot_dashboard(request):
    if not request.user.userprofile.is_staff:
        if request.method == 'POST':
            flight_number = request.POST['flight_number']
            departure_location = request.POST['departure_location']
            arrival_location = request.POST['arrival_location']
            status = request.POST['status']
            estimated_arrival_time = request.POST['estimated_arrival_time']

            flight, created = Flight.objects.get_or_create(
                flight_number=flight_number,
                defaults={
                    'departure_location': departure_location,
                    'arrival_location': arrival_location,
                    'status': status,
                    'estimated_arrival_time': estimated_arrival_time
                }
            )
            if not created:
                flight.departure_location = departure_location
                flight.arrival_location = arrival_location
                flight.status = status
                flight.estimated_arrival_time = estimated_arrival_time
                flight.save()

            messages.success(request, 'Flight information updated.')

        flights = Flight.objects.all()
        return render(request, 'pilot_dashboard.html', {'flights': flights})
    return HttpResponse("Unauthorized", status=401)

# Function to update flight status
@login_required
def update_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_statuses = data.get('selected_statuses', [])
        for status_info in selected_statuses:
            flight_number, status = status_info.split(':')
            flight = Flight.objects.get(flight_number=flight_number)
            flight.status = status
            flight.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# Function to clear the flight table
@login_required
def clear_table(request):
    if request.method == 'POST':
        Flight.objects.all().delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# Function to get the nearest airport
def get_nearest_airport(city_name):
    api_key = 'o4PqxkiTH1BW7UuJkYqLCg==Mi19hEEKZDneaDNC'
    headers = {
        'X-RapidAPI-Key': api_key,
        'X-RapidAPI-Host': 'wft-geo-db.p.rapidapi.com'
    }

    # Step 1: Get the geolocation of the city
    city_url = f'https://wft-geo-db.p.rapidapi.com/v1/geo/cities'
    city_params = {'namePrefix': city_name}
    city_response = requests.get(city_url, headers=headers, params=city_params)
    
    if city_response.status_code != 200:
        logger.error(f"Error fetching city data: {city_response.status_code} - {city_response.text}")
        return "Unknown Airport"

    city_data = city_response.json()
    if 'data' not in city_data or not city_data['data']:
        logger.error(f"No data found for city: {city_name}")
        return "Unknown Airport"

    city_info = city_data['data'][0]
    latitude = city_info['latitude']
    longitude = city_info['longitude']

    # Step 2: Find the nearest airport to the city's geolocation
    airport_url = f'https://wft-geo-db.p.rapidapi.com/v1/geo/locations/{latitude}{longitude}/nearbyAirports'
    airport_params = {
        'radius': 100,  # search within 100 km radius
        'limit': 1      # get the nearest airport
    }
    airport_response = requests.get(airport_url, headers=headers, params=airport_params)

    if airport_response.status_code != 200:
        logger.error(f"Error fetching airport data: {airport_response.status_code} - {airport_response.text}")
        return "Unknown Airport"

    airport_data = airport_response.json()
    if 'data' not in airport_data or not airport_data['data']:
        logger.error(f"No airport data found for location: {latitude}, {longitude}")
        return "Unknown Airport"

    nearest_airport = airport_data['data'][0]
    return nearest_airport['name']

# Function to get weather info and possibly divert the flight
@login_required
def get_weather_info(request, flight_number):
    try:
        flight = Flight.objects.get(flight_number=flight_number)
    except Flight.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Flight not found'})

    arrival_location = flight.arrival_location
    api_key = '2a12086c7431fc7c4a964dc3aa4bb27b'
    current_weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={arrival_location}&appid={api_key}"
    response = requests.get(current_weather_url)
    data = response.json()

    if data['cod'] == 200:
        weather_data = {
            'city': data['name'],
            'temperature': temp_celsius(data['main']['temp']),
            'feels_like': temp_celsius(data['main']['feels_like']),
            'temp_min': temp_celsius(data['main']['temp_min']),
            'temp_max': temp_celsius(data['main']['temp_max']),
            'pressure': data['main']['pressure'],
            'humidity': data['main']['humidity'],
            'visibility': data.get('visibility', 0),
            'wind_speed': data['wind']['speed'],
            'wind_deg': data['wind']['deg'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon'],
            'country': data['sys']['country'],
            'sunrise': time_format(data['sys']['sunrise']),
            'sunset': time_format(data['sys']['sunset']),
        }

        # Check if the weather conditions meet the requirements for standard aircraft
        if weather_data['visibility'] < 5000 or weather_data['wind_speed'] > 15:
            nearest_airport = get_nearest_airport(arrival_location)
            flight.arrival_location = nearest_airport
            flight.status = 'Diverted'
            flight.save()

        return JsonResponse({'success': True, 'weather_data': weather_data})
    else:
        return JsonResponse({'success': False, 'message': 'Could not fetch weather data'})
