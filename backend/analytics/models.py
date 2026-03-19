from django.db import models
from django.utils import timezone


class TicketMetrics(models.Model):
    """Pre‑computed metrics for each ticket to power dashboards and ML models"""
    ticket = models.OneToOneField('tickets.Ticket', on_delete=models.CASCADE, related_name='metrics')

    # Time metrics (in seconds)
    first_response_time = models.PositiveIntegerField(null=True, blank=True,
                                                       help_text="Seconds from creation to first agent response")
    resolution_time = models.PositiveIntegerField(null=True, blank=True,
                                                   help_text="Seconds from creation to resolution")
    time_to_assign = models.PositiveIntegerField(null=True, blank=True,
                                                  help_text="Seconds from creation to first assignment")

    # Counts
    escalation_count = models.PositiveSmallIntegerField(default=0)
    reassignment_count = models.PositiveSmallIntegerField(default=0)
    message_count = models.PositiveSmallIntegerField(default=0)
    agent_message_count = models.PositiveSmallIntegerField(default=0)
    customer_message_count = models.PositiveSmallIntegerField(default=0)

    # Flags
    sla_breached_response = models.BooleanField(default=False)
    sla_breached_resolution = models.BooleanField(default=False)

    # Last updated
    updated_at = models.DateTimeField(auto_now=True)
    ticket_created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Ticket metrics"

    def __str__(self):
        return f"Metrics for {self.ticket.ticket_number}"

class SLAMetric(models.Model):
    date = models.DateField(unique=True)
    tickets_opened = models.IntegerField(default=0)
    tickets_resolved = models.IntegerField(default=0)
    avg_response_time = models.FloatField(null=True, blank=True)  # in hours
    avg_resolution_time = models.FloatField(null=True, blank=True)
    breached_response = models.IntegerField(default=0)
    breached_resolution = models.IntegerField(default=0)
    escalated_tickets = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']