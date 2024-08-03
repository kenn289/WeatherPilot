
from django.contrib import admin
from .models import UserProfile, Weather, Flight

admin.site.register(UserProfile)
admin.site.register(Weather)
admin.site.register(Flight)
