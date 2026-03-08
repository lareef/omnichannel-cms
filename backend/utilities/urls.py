from django.urls import path
from . import views

app_name = 'utilities'

urlpatterns = [
    # ... existing URLs ...

    # Calendar Management (admin only)
    path('calendars/', views.CalendarListView.as_view(), name='calendar_list'),
    path('calendars/add/', views.CalendarCreateView.as_view(), name='calendar_add'),
    path('calendars/<int:pk>/', views.CalendarDetailView.as_view(), name='calendar_detail'),
    path('calendars/<int:pk>/edit/', views.CalendarUpdateView.as_view(), name='calendar_edit'),
    path('calendars/<int:pk>/delete/', views.CalendarDeleteView.as_view(), name='calendar_delete'),

    # Business Hour Rules
    path('calendars/<int:calendar_pk>/hours/add/', views.BusinessHourRuleCreateView.as_view(), name='businesshour_add'),
    path('hours/<int:pk>/edit/', views.BusinessHourRuleUpdateView.as_view(), name='businesshour_edit'),
    path('hours/<int:pk>/delete/', views.BusinessHourRuleDeleteView.as_view(), name='businesshour_delete'),

    # Holidays
    path('calendars/<int:calendar_pk>/holidays/add/', views.HolidayCreateView.as_view(), name='holiday_add'),
    path('holidays/<int:pk>/edit/', views.HolidayUpdateView.as_view(), name='holiday_edit'),
    path('holidays/<int:pk>/delete/', views.HolidayDeleteView.as_view(), name='holiday_delete'),
]