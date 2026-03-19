# accounts/tasks.py
from celery import shared_task
from allauth.account.models import EmailAddress

@shared_task(bind=True, max_retries=3)
def send_verification_email_task(self, email_address_id, signup=True):
    """
    Send verification email asynchronously using the EmailAddress instance.
    """
    try:
        email_address = EmailAddress.objects.get(id=email_address_id)
        # send_confirmation() accepts an optional request object (can be None)
        email_address.send_confirmation(request=None, signup=signup)
    except EmailAddress.DoesNotExist:
        # Log or ignore – the email address might have been deleted
        pass
    except Exception as exc:
        # Retry on failure (e.g., SMTP timeout)
        self.retry(exc=exc, countdown=60)