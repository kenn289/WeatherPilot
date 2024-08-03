from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('about_us/', views.about_us, name='about_us'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('staff_dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('pilot_dashboard/', views.pilot_dashboard, name='pilot_dashboard'),
    path('update_status/', views.update_status, name='update_status'),
    path('clear_table/', views.clear_table, name='clear_table'),
    path('get_weather_info/<str:flight_number>/', views.get_weather_info, name='get_weather_info'),
]
