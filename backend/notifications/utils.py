from .models import Notification
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from .models import Notification
from .tasks import send_email_notification  # we'll create this task
def send_notification(user, title, message, related_object=None):
    # Store in DB
    notif = Notification.objects.create(
        recipient=user,
        type='in_app',
        title=title,
        content=message,
        related_object=related_object
    )
    # Also send email if user prefers
    if user.preferences.notify_email:
        send_mail(
            subject=title,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    # You could also trigger a Celery task for async sending
    
def create_notification(recipient, title, message, related_object=None, send_email=False):
    """
    Create an in‑app notification and optionally queue an email.
    """
    notif = Notification.objects.create(
        recipient=recipient,
        type='in_app' if not send_email else 'email',
        title=title,
        content=message,
        related_object=related_object,
        status='pending'
    )
    if send_email and recipient.email:
        # Queue email via Celery
        send_email_notification.delay(
            recipient_id=recipient.id,
            subject=title,
            message=message,
            notification_id=notif.id
        )
    return notif


def notify_ticket_update(ticket, changes, updated_by):
    """
    Create notifications based on ticket changes.
    """
    from tickets.models import Ticket
    recipients = set()

    # ---- Assignment changes ----
    if 'old_assigned_to' in changes or 'new_assigned_to' in changes:
        old = changes.get('old_assigned_to')
        new = changes.get('new_assigned_to')

        # Notify new assignee
        if new and new != updated_by:
            recipients.add(new)
            title = f"Ticket #{ticket.ticket_number} assigned to you"
            message = f"Ticket '{ticket.subject}' has been assigned to you by {updated_by.get_full_name()}."
            create_notification(new, title, message, related_object=ticket, send_email=True)

        # Notify old assignee (if they are not the updater and not the same as new)
        if old and old != updated_by and old != new:
            recipients.add(old)
            title = f"Ticket #{ticket.ticket_number} reassigned"
            message = f"Ticket '{ticket.subject}' has been reassigned from you to {new.get_full_name() if new else 'unassigned'} by {updated_by.get_full_name()}."
            create_notification(old, title, message, related_object=ticket, send_email=True)

    # ---- Status changes ----
    if 'old_status' in changes or 'new_status' in changes:
        old = changes.get('old_status')
        new = changes.get('new_status')

        # Notify assigned agent
        if ticket.assigned_to and ticket.assigned_to != updated_by:
            recipients.add(ticket.assigned_to)
            title = f"Ticket #{ticket.ticket_number} status changed"
            message = f"Status of ticket '{ticket.subject}' changed from '{old.name if old else 'None'}' to '{new.name if new else 'None'}' by {updated_by.get_full_name()}."
            create_notification(ticket.assigned_to, title, message, related_object=ticket, send_email=True)

        # If status is a closed state, optionally notify the customer
        if new and new.is_closed_state and ticket.customer_email:
            # We don't have a user object for customer, so we can send email directly
            # but we might also create an in-app notification for a virtual customer (if we had a customer user)
            # For now, send email via Celery without creating notification record
            from .tasks import send_customer_email
            send_customer_email.delay(
                recipient_email=ticket.customer_email,
                subject=f"Your ticket #{ticket.ticket_number} has been resolved",
                message=f"Your ticket '{ticket.subject}' has been marked as {new.name}. Thank you for your patience."
            )

    # Could also notify department supervisors, etc.
    return recipients
