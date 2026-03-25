"""
 - Handles single ticket when ticket_id is provided.

 - Batch updates – when called without an argument, processes tickets updated in the last hour (good for periodic scheduling).

 - Efficient queries using select_related? Not used here because we iterate one by one, but for bulk it's okay. If you have thousands of tickets per hour, you might want to optimise further (e.g., using prefetch_related). For now, it's simple.

 - Graceful handling of missing ticket_created_at field – it uses hasattr to avoid errors."""

import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from tickets.models import Ticket, Message, TicketUpdate, TicketEscalation
from .models import TicketMetrics

logger = logging.getLogger(__name__)


@shared_task
def refresh_ticket_metrics(ticket_id=None):
    """
    Update TicketMetrics for a single ticket or for all tickets updated in the last hour.
    """
    print("Updating TicketMetrics... @ ", timezone.now() )
    
    if ticket_id:
        tickets = Ticket.objects.filter(id=ticket_id)
    else:
        # Process tickets that were updated in the last hour
        last_hour = timezone.now() - timedelta(hours=1)
        tickets = Ticket.objects.filter(updated_at__gte=last_hour)

    for ticket in tickets:
        metrics, created = TicketMetrics.objects.get_or_create(ticket=ticket)

        # --- First response time (seconds) ---
        first_response = ticket.messages.filter(
            sender_type='agent', is_internal_note=False
        ).order_by('sent_at').first()
        if first_response:
            delta = first_response.sent_at - ticket.created_at
            metrics.first_response_time = int(delta.total_seconds())
        else:
            metrics.first_response_time = None

        # --- Resolution time (seconds) ---
        if ticket.resolved_at:
            delta = ticket.resolved_at - ticket.created_at
            metrics.resolution_time = int(delta.total_seconds())
        else:
            metrics.resolution_time = None

        # --- Time to first assignment (seconds) ---
        first_assignment = ticket.updates.filter(
            update_type='other',
            old_assigned_to__isnull=True,
            new_assigned_to__isnull=False
        ).order_by('created_at').first()
        if first_assignment:
            delta = first_assignment.created_at - ticket.created_at
            metrics.time_to_assign = int(delta.total_seconds())
        else:
            metrics.time_to_assign = None

        # --- Counts ---
        metrics.escalation_count = ticket.escalations.count()
        metrics.reassignment_count = ticket.updates.filter(
            update_type='other',
            old_assigned_to__isnull=False,
            new_assigned_to__isnull=False
        ).count()
        metrics.message_count = ticket.messages.count()
        metrics.agent_message_count = ticket.messages.filter(
            sender_type='agent', is_internal_note=False
        ).count()
        metrics.customer_message_count = ticket.messages.filter(
            sender_type='customer'
        ).count()

        # --- SLA breach flags ---
        metrics.sla_breached_response = ticket.is_response_breached
        metrics.sla_breached_resolution = ticket.is_resolution_breached

        # --- Denormalised ticket creation date (if the field exists) ---
        # Some models have 'ticket_created_at'; if not, skip or add it later.
        # We'll check if the field exists to avoid errors.
        if hasattr(metrics, 'ticket_created_at'):
            metrics.ticket_created_at = ticket.created_at

        metrics.save()

        logger.debug(f"Updated metrics for ticket {ticket.ticket_number} (created={created})")