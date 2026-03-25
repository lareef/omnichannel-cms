import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from .models import Ticket, EscalationPolicy, EscalationTarget, TicketEscalation
from notifications.utils import send_notification, notify_admins
from accounts.models import User, Role, Department

logger = logging.getLogger(__name__)


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
        # Trigger escalation check
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
    """Check and apply escalation policies for a specific ticket."""
    ticket = Ticket.objects.get(id=ticket_id)
    now = timezone.now()
    
    # Find applicable escalation policies
    policies = EscalationPolicy.objects.filter(
        Q(sla_rule__priority=ticket.priority) | Q(sla_rule__isnull=True),
        Q(sla_rule__department=ticket.department) | Q(sla_rule__department__isnull=True),
        is_active=True
    ).order_by('level')
    
    for policy in policies:
        if should_escalate(ticket, policy, now):
            # Check if already escalated at this level
            if not TicketEscalation.objects.filter(
                ticket=ticket,
                level=policy.level,
                is_resolved=False
            ).exists():
                # Get the target for this policy level
                target = policy.get_target_for_level()
                if not target:
                    continue
                    
                # Determine who to escalate to
                escalated_to_user = None
                if target.escalate_to_user:
                    escalated_to_user = target.escalate_to_user
                elif target.escalate_to_role:
                    # Find a user with that role in the same department
                    users = User.objects.filter(
                        role=target.escalate_to_role,
                        department=ticket.department
                    ).first()
                    if users:
                        escalated_to_user = users
                elif target.escalate_to_department:
                    # Find department head or supervisor
                    users = User.objects.filter(
                        department=target.escalate_to_department,
                        role__name__icontains='head'
                    ).first()
                    if users:
                        escalated_to_user = users
                
                if escalated_to_user:
                    # Create escalation record
                    escalation = TicketEscalation.objects.create(
                        ticket=ticket,
                        escalated_to=escalated_to_user,
                        reason=f"Escalation policy: {policy.name} (Level {policy.level})",
                        level=policy.level,
                        escalated_at=now
                    )
                    
                    # Send notification
                    send_notification(
                        user=escalated_to_user,
                        title=f"Ticket #{ticket.ticket_number} Escalated (Level {policy.level})",
                        message=f"Ticket '{ticket.subject}' requires attention. Reason: {policy.get_trigger_event_display()}",
                        related_object=ticket
                    )
                    
                    # Update ticket escalation level
                    ticket.is_escalated = True
                    ticket.escalation_level = max(ticket.escalation_level, policy.level)
                    ticket.save(update_fields=['is_escalated', 'escalation_level'])
                    
                    print(f"Escalated ticket {ticket.ticket_number} to level {policy.level}")

# @shared_task
# def check_escalations():
#     """Periodic task to evaluate all active tickets for escalations."""
#     now = timezone.now()

#     # Get all active tickets (not resolved, not archived)
#     tickets = Ticket.objects.filter(
#         resolved_at__isnull=True,
#         is_archived=False
#     ).select_related('priority', 'department', 'assigned_to')

#     # Get all active escalation policies
#     policies = EscalationPolicy.objects.filter(is_active=True)

#     for ticket in tickets:
#         check_escalation_for_ticket.delay(ticket.id)

@shared_task
def check_escalations():
    """
    Periodic task: evaluate all active tickets against escalation policies.
    """
    now = timezone.now()
    print("Checking for Escalations... @ ", now )
    # Get all active tickets (not resolved, not archived)
    tickets = Ticket.objects.filter(
        resolved_at__isnull=True,
        is_archived=False
    ).select_related('priority', 'department', 'assigned_to')

    # Get all active escalation policies
    policies = EscalationPolicy.objects.filter(is_active=True)

    for ticket in tickets:
        # For each ticket, find applicable policies (could be filtered by priority/department etc.)
        # In a more advanced version, you might filter policies by SLA rule, but for now we take all.
        for policy in policies:
            # Skip if already escalated at this level and not resolved
            if TicketEscalation.objects.filter(
                ticket=ticket,
                level=policy.level,
                is_resolved=False
            ).exists():
                continue

            if should_escalate(ticket, policy, now):
                # Determine escalation target
                target_user = None
                if policy.escalate_to_user:
                    target_user = policy.escalate_to_user
                elif policy.escalate_to_role:
                    # Get any user with that role? In a real system, you might need logic to pick.
                    # For simplicity, we'll pick the first active user with that role in the same department.
                    users = ticket.department.user_set.filter(
                        role=policy.escalate_to_role,
                        is_active=True
                    )
                    if users.exists():
                        target_user = users.first()
                # If no target, fallback to admins (or skip)
                if not target_user:
                    # Notify all admins
                    target_user = None  # we'll handle this in notification
                # Create escalation record
                escalation = TicketEscalation.objects.create(
                    ticket=ticket,
                    escalated_to=target_user,
                    reason=f"Escalation policy: {policy.name} (Level {policy.level})",
                    level=policy.level,
                    escalated_at=now
                )
                # Update ticket escalation level
                if not ticket.is_escalated or ticket.escalation_level < policy.level:
                    ticket.is_escalated = True
                    ticket.escalation_level = policy.level
                    ticket.save(update_fields=['is_escalated', 'escalation_level'])

                # Send notification
                if target_user:
                    # You could use notify_admins with role, but here we just send to specific user
                    # For now, we'll reuse notify_admins with role=None, but we need a user-specific version.
                    # Let's create a generic notification function (notify_user) in notifications/utils.
                    from notifications.utils import notify_user
                    notify_user(
                        user=target_user,
                        title=f"Ticket #{ticket.ticket_number} escalated (Level {policy.level})",
                        message=f"Ticket '{ticket.subject}' requires attention.\nReason: {policy.name}",
                        related_object=ticket,
                        send_email=True
                    )
                else:
                    # If no specific target, notify all admins
                    notify_admins(
                        subject=f"Ticket #{ticket.ticket_number} escalated (Level {policy.level})",
                        message=f"Ticket '{ticket.subject}' requires attention.\nReason: {policy.name}",
                        related_object=ticket,
                        role='admin'  # only admins
                    )

                # Log (optional)
                logger.info(f"Escalated ticket {ticket.ticket_number} to level {policy.level} by policy {policy.name}")

def should_escalate(ticket, policy, now):
    """Determine if a ticket meets the escalation criteria for a policy."""
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
        # Find last assignment time from TicketUpdate
        last_assignment = ticket.updates.filter(
            update_type='assignment_change'
        ).order_by('-created_at').first()
        if last_assignment:
            delta = now - last_assignment.created_at
            return delta.total_seconds() / 60 >= policy.threshold_minutes
        return False
    elif policy.trigger_event == 'no_activity':
        if not policy.threshold_minutes:
            return False
        # Check last message or update
        last_message = ticket.messages.order_by('-sent_at').first()
        last_update = ticket.updates.order_by('-created_at').first()
        
        last_activity = ticket.created_at
        if last_message and last_message.sent_at > last_activity:
            last_activity = last_message.sent_at
        if last_update and last_update.created_at > last_activity:
            last_activity = last_update.created_at
            
        delta = now - last_activity
        return delta.total_seconds() / 60 >= policy.threshold_minutes
    return False

def get_next_escalation_target(ticket, current_level):
    """Get the next escalation target for a ticket based on current level."""
    # Find policies with level > current_level
    policies = EscalationPolicy.objects.filter(
        Q(sla_rule__priority=ticket.priority) | Q(sla_rule__isnull=True),
        Q(sla_rule__department=ticket.department) | Q(sla_rule__department__isnull=True),
        is_active=True,
        level__gt=current_level
    ).order_by('level').first()
    
    if policies:
        target = policies.get_target_for_level()
        return target, policies.level
    return None, None
