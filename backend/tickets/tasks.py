from celery import shared_task
from django.utils import timezone
from .models import Ticket, EscalationPolicy, TicketEscalation
from notifications.utils import send_notification, notify_admins
from django.db.models import Q

@shared_task
def check_sla_breaches():
    print("Checking for SLA breaches... @ ", timezone.now() )
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
                
@shared_task
def check_escalations():
    """Periodic task to evaluate all active tickets for escalations."""
    now = timezone.now()

    # Get all active tickets (not resolved, not archived)
    tickets = Ticket.objects.filter(
        resolved_at__isnull=True,
        is_archived=False
    ).select_related('priority', 'department', 'assigned_to')

    for ticket in tickets:
        # Find applicable policies (could be cached)
        policies = EscalationPolicy.objects.filter(
            Q(sla_rule__priority=ticket.priority) |
            Q(sla_rule__isnull=True)
        ).filter(
            Q(sla_rule__department=ticket.department) |
            Q(sla_rule__department__isnull=True)
        )

        for policy in policies:
            if should_escalate(ticket, policy, now):
                # Check if already escalated at this level
                if not TicketEscalation.objects.filter(
                    ticket=ticket,
                    level=policy.level,
                    is_resolved=False
                ).exists():
                    # Create escalation
                    escalation = TicketEscalation.objects.create(
                        ticket=ticket,
                        escalated_to=policy.escalate_to_user,
                        reason=f"Escalation policy: {policy.name}",
                        level=policy.level,
                        escalated_at=now
                    )
                    # Notify the target user/role
                    if policy.escalate_to_user:
                        notify_admins(
                            subject=f"Ticket #{ticket.ticket_number} escalated (Level {policy.level})",
                            message=f"Ticket '{ticket.subject}' requires attention.",
                            related_object=ticket,
                            role=policy.escalate_to_role.code if policy.escalate_to_role else None,
                        )
                    # Optionally update ticket escalation level
                    ticket.is_escalated = True
                    ticket.escalation_level = max(ticket.escalation_level, policy.level)
                    ticket.save(update_fields=['is_escalated', 'escalation_level'])

def should_escalate(ticket, policy, now):
    """Determine if a ticket meets the escalation criteria."""
    if policy.trigger_event == 'response_breach':
        return ticket.is_response_breached
    elif policy.trigger_event == 'resolution_breach':
        return ticket.is_resolution_breached
    elif policy.trigger_event == 'time_since_creation':
        if not policy.threshold_minutes:
            return False
        delta = now - ticket.created_at
        return delta.total_seconds() / 60 >= policy.threshold_minutes
    elif policy.trigger_event == 'time_since_assignment':
        if not ticket.assigned_to or not policy.threshold_minutes:
            return False
        # We need assignment history – you may need to track last assignment change
        # For simplicity, we'll skip this or implement via TicketUpdate
        return False
    elif policy.trigger_event == 'no_activity':
        # Check last message/update time
        last_activity = ticket.updated_at  # or last message
        if not policy.threshold_minutes:
            return False
        delta = now - last_activity
        return delta.total_seconds() / 60 >= policy.threshold_minutes
    return False