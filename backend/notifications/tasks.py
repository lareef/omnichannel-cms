from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
from django.utils import timezone


@shared_task
def send_email_notification(recipient_id, subject, message, notification_id=None):
    """
    Send an email and update notification status.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(id=recipient_id)
        if user.email:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            if notification_id:
                Notification.objects.filter(id=notification_id).update(status='sent', sent_at=timezone.now())
        else:
            if notification_id:
                Notification.objects.filter(id=notification_id).update(status='failed', error_message="No email address")
    except Exception as e:
        if notification_id:
            Notification.objects.filter(id=notification_id).update(status='failed', error_message=str(e))


@shared_task
def send_customer_email(recipient_email, subject, message):
    """
    Send email to a customer (no user account).
    """
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        fail_silently=False,
    )