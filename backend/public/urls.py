from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='landing'),
    path('track/', views.track_entry, name='track_entry'),
    path('track/<str:token>/', views.track_ticket, name='track_ticket'),
    path('submit/', views.submit_complaint, name='submit_complaint'),
]