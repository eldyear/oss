from django.urls import path
from . import views
from . import admin

urlpatterns = [
    path('tablo_dep/<str:lang>/', views.tablo_dep, name='tablo_dep'),
    path('tablo_arr/<str:lang>/', views.tablo_arr, name='tablo_arr'),
    path('dep/', views.departure, name='departure'),
    path('arr/', views.arrival, name='arrival'),
    path('iframe_dep/', views.iframe_dep, name='iframe_dep'),
    path('iframe_arr/', views.iframe_arr, name='iframe_arr'),
    path('deparr/', views.deparr, name='deparr'),
    path('ch/<int:pk>/', views.check_ajax, name='check_in_desk_ajax'),
    path('gate/<int:pk>/', views.gate, name='gate'),
    path('bag/<int:pk>/', views.baggage, name='baggage'),
    path('main/', views.my_urls, name='main'),
    path('get_flight_data_check/<str:lang>/<int:pk>/', views.get_flight_data_check, name='get_flight_data_check'),
    path('get_flight_data_gate/<str:lang>/G<int:pk>/', views.get_flight_data_gate, name='get_flight_data_gate'),
    path('get_flight_data_bag/<str:lang>/<int:pk>/', views.get_flight_data_bag, name='get_flight_data_bag'),
    path('generate-daily-schedule/', admin.generate_daily_schedule_view, name='generate_daily_schedule'),
    path('', views.my_urls, name='main'),
]
