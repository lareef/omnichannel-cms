from .models import Notification
from django.core.mail import send_mail
from django.conf import settings

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