from django.db import models


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

    class Meta:
        verbose_name_plural = "Ticket metrics"

    def __str__(self):
        return f"Metrics for {self.ticket.ticket_number}"
