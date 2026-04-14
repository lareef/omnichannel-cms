from django.urls import path
from . import views

# app_name = 'public'

urlpatterns = [
    path('', views.home, name='landing'),
    path('track/', views.track_entry, name='track_entry'),
    path('track/<str:token>/', views.track_ticket, name='track_ticket'),
    path('submit/', views.submit_complaint, name='submit_complaint'),
    
    path('api/whatsapp-webhook/', views.whatsapp_webhook, name='whatsapp_webhook'),
    # path('ticket/<int:ticket_id>/send-whatsapp-reply/', views.send_whatsapp_reply, name='send_whatsapp_reply'),
]