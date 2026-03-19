from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('sla/', views.SLADashboardView.as_view(), name='sla_dashboard'),
    path('api/sla-chart-data/', views.sla_chart_data, name='sla_chart_data'),
    path('api/sla-metrics/', views.sla_performance_metrics, name='sla_metrics'),
    
    # analytics/urls.py with HTMX
    path('partials/kpi-cards/', views.kpi_cards_partial, name='sla_metrics_partial'),
    path('partials/trend-chart/', views.trend_chart_partial, name='trend_chart_partial'),
    path('partials/breach-chart/', views.breach_chart_partial, name='breach_chart_partial'),
]