from django.contrib import admin
from .models import TicketMetrics, SLAMetric


@admin.register(TicketMetrics)
class TicketMetricsAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'first_response_time', 'resolution_time', 'reassignment_count', 'updated_at')
    list_filter = ('sla_breached_response', 'sla_breached_resolution')
    search_fields = ('ticket__ticket_number',)
    readonly_fields = ('updated_at',)


@admin.register(SLAMetric)
class SLAMetricAdmin(admin.ModelAdmin):
    list_display = ('date', 'tickets_opened', 'tickets_resolved', 'avg_response_time', 'avg_resolution_time', 'updated_at')
    list_filter = ('date',)
    readonly_fields = ('created_at', 'updated_at')
