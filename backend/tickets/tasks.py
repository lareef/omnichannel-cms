from celery import shared_task
from django.utils import timezone
from .models import Ticket, EscalationPolicy, TicketEscalation
from notifications.utils import send_notification
from django.db.models import Q

@shared_task
def check_sla_breaches():
    now = timezone.now()
    # Response breaches
    response_breached = Ticket.objects.filter(
        response_due_at__lt=now,
        first_response_at__isnull=True,
        is_response_breached=False
    )
    for ticket in response_breached:
        ticket.is_response_breached = True
        ticket.save(update_fields=['is_response_breached'])
        # Optionally trigger escalation
        check_escalation_for_ticket.delay(ticket.id)

    # Resolution breaches
    resolution_breached = Ticket.objects.filter(
        resolution_due_at__lt=now,
        resolved_at__isnull=True,
        is_resolution_breached=False
    )
    for ticket in resolution_breached:
        ticket.is_resolution_breached = True
        ticket.save(update_fields=['is_resolution_breached'])
        check_escalation_for_ticket.delay(ticket.id)

@shared_task
def check_escalation_for_ticket(ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    # Find applicable escalation policies based on ticket properties
    # For simplicity, assume we have a method
    policies = EscalationPolicy.objects.filter(
        Q(sla_rule__priority=ticket.priority) |
        Q(sla_rule__isnull=True)
    )
    for policy in policies:
        if policy.should_escalate(ticket):
            TicketEscalation.objects.create(
                ticket=ticket,
                escalated_to=policy.escalate_to_user,
                reason=f"Escalation policy: {policy.name}",
                level=policy.level
            )
            # Send notification
            if policy.escalate_to_user:
                send_notification(
                    user=policy.escalate_to_user,
                    title="Ticket Escalated",
                    message=f"Ticket {ticket.ticket_number} requires attention."
                )