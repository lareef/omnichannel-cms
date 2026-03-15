We'll create a reusable admin notification utility that can be called from anywhere in your project (e.g., after user signup, ticket escalation, SLA breach, etc.). It will:

Send an in‑app notification to all admin users (superusers and users with role 'admin').

Optionally send an email to those admins asynchronously via Celery.

Link the notification to a related object (like the new user, ticket, etc.) for easy reference.

1. Create the Utility Function
Place this in notifications/utils.py:

python
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Notification
from .tasks import send_email_notification

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
2. Ensure Celery Task Exists
You should already have send_email_notification in notifications/tasks.py. If not, here it is:

python
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Notification

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
3. Call the Utility Where Needed
Example 1: After New User Signup (Pending Approval)
In your accounts/forms.py (inside CustomSignupForm.save):

python
from notifications.utils import notify_admins

class CustomSignupForm(SignupForm):
    def save(self, request):
        user = super().save(request)
        user.is_active = False  # require admin approval
        user.save(update_fields=['is_active'])

        # Notify admins
        notify_admins(
            subject="New user registration pending approval",
            message=f"User {user.username} ({user.email}) has signed up and requires activation.",
            related_object=user,
            send_email=True
        )
        return user
Example 2: Ticket Escalation
Inside your escalation logic (e.g., in a Celery task or view):

python
from notifications.utils import notify_admins

# When a ticket is escalated to level 2 or higher
if ticket.escalation_level >= 2:
    notify_admins(
        subject=f"Ticket #{ticket.ticket_number} escalated to level {ticket.escalation_level}",
        message=f"Ticket '{ticket.subject}' requires immediate attention.",
        related_object=ticket,
        send_email=True
    )
Example 3: SLA Breach
In your SLA breach detection task:

python
if ticket.is_response_breached:
    notify_admins(
        subject=f"SLA Response Breach: Ticket #{ticket.ticket_number}",
        message=f"Response due date passed for ticket '{ticket.subject}'.",
        related_object=ticket,
        send_email=True
    )
4. Display Notifications in UI
Your base.html already has a notification dropdown that shows unread notifications. Admins will see these alerts immediately. The email will be sent asynchronously.

5. Make It Global and Reusable
You can now import notify_admins anywhere in your project and call it whenever a critical event occurs that requires admin attention. This centralises your notification logic and ensures consistency.

If you need to notify a different group (e.g., all supervisors), you can create a similar function notify_supervisors or extend the utility to accept a role parameter. For now, this covers admins.

We'll enhance the notify_admins utility to accept a role parameter, making it flexible enough to notify any group of users (admins, supervisors, agents, etc.) while keeping backward compatibility. You can pass a single role code or a list of role codes.

Here's the updated function:

python
# notifications/utils.py
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Notification
from .tasks import send_email_notification

User = get_user_model()

def notify_admins(subject, message, related_object=None, send_email=True, role=None):
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
✅ How to use it:
1. Notify admins (default behaviour)
python
notify_admins(
    subject="New user registered",
    message="User jdoe has signed up and needs approval.",
    related_object=new_user
)
2. Notify supervisors only
python
notify_admins(
    subject="Ticket escalated",
    message="Ticket #12345 requires supervisor attention.",
    role='supervisor'
)
3. Notify both supervisors and admins
python
notify_admins(
    subject="SLA breach",
    message="Response overdue for ticket #12345.",
    role=['supervisor', 'admin']
)
4. Notify all agents
python
notify_admins(
    subject="New ticket assigned",
    message="Ticket #12345 has been assigned to you.",
    role='agent'
)
