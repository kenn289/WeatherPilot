from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    bio = models.TextField(blank=True)
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    city = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Weather(models.Model):
    city = models.CharField(max_length=100)
    temperature = models.FloatField()
    feels_like = models.FloatField()
    temp_min = models.FloatField()
    temp_max = models.FloatField()
    pressure = models.IntegerField()
    humidity = models.IntegerField()
    visibility = models.IntegerField()
    wind_speed = models.FloatField()
    wind_deg = models.IntegerField()
    description = models.CharField(max_length=255)
    icon = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    sunrise = models.DateTimeField()
    sunset = models.DateTimeField()

    def __str__(self):
        return f"{self.city} - {self.temperature}°C"

class Flight(models.Model):
    flight_number = models.CharField(max_length=10)
    departure_location = models.CharField(max_length=100)
    arrival_location = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    estimated_arrival_time = models.DateTimeField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.flight_number
