from .models import Notification
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from .models import Notification
from .tasks import send_email_notification  # we'll create this task
from django.contrib.auth import get_user_model
from django.db.models import Q
from celery import shared_task
from django.utils import timezone


User = get_user_model()

def notify_admins(subject, message, related_object=None, send_email=True):
    """
    Send notification to all admin users (superusers and users with admin role).
    Creates in‑app notification and optionally sends email asynchronously.

    Args:
        subject (str): Short title for the notification.
        message (str): Detailed message.
        related_object (Model instance, optional): Django model instance to link.
        send_email (bool): Whether to also send an email.
    """
    # Get all admin users: superusers OR users with role code 'admin'
    admins = User.objects.filter(
        Q(is_superuser=True) | Q(role__code='admin')
    ).distinct()

    for admin in admins:
        # Create in‑app notification
        notif = Notification.objects.create(
            recipient=admin,
            type='in_app',
            title=subject,
            content=message,
            related_object=related_object,
            status='pending'
        )
        # Queue email if requested and admin has an email address
        if send_email and admin.email:
            send_email_notification.delay(
                recipient_id=admin.id,
                subject=subject,
                message=message,
                notification_id=notif.id
            )

# notifications/utils.py
def notify_roles(subject, message, related_object=None, send_email=True, role=None):
    """
    Send notification to users with specified roles.
    If role is None, defaults to superusers and users with role code 'admin' (original behavior).

    Args:
        subject (str): Short title for the notification.
        message (str): Detailed message.
        related_object (Model instance, optional): Django model instance to link.
        send_email (bool): Whether to also send an email.
        role (str or list): Role code(s) to notify. If None, uses default admin+superuser.
    """
    # Build query based on role parameter
    if role is None:
        # Default: superusers OR role='admin'
        query = Q(is_superuser=True) | Q(role__code='admin')
    else:
        # Convert single string to list
        if isinstance(role, str):
            role_codes = [role]
        else:
            role_codes = role
        query = Q(role__code__in=role_codes)

    users = User.objects.filter(query).distinct()

    for user in users:
        # Create in‑app notification
        notif = Notification.objects.create(
            recipient=user,
            type='in_app',
            title=subject,
            content=message,
            related_object=related_object,
            status='pending'
        )
        # Queue email if requested and user has an email address
        if send_email and user.email:
            send_email_notification.delay(
                recipient_id=user.id,
                subject=subject,
                message=message,
                notification_id=notif.id
            )
            
@shared_task
def send_email_notification(recipient_id, subject, message, notification_id=None):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(id=recipient_id)
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        if notification_id:
            Notification.objects.filter(id=notification_id).update(
                status='sent',
                sent_at=timezone.now()
            )
    except Exception as e:
        if notification_id:
            Notification.objects.filter(id=notification_id).update(
                status='failed',
                error_message=str(e)
            )
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
