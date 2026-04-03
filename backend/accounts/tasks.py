# accounts/tasks.py
# from celery import shared_task
# from allauth.account.models import EmailAddress

# @shared_task(bind=True, max_retries=3)
# def send_verification_email_task(self, email_address_id, signup=True):
#     """
#     Send verification email asynchronously using the EmailAddress instance.
#     """
#     try:
#         email_address = EmailAddress.objects.get(id=email_address_id)
#         # send_confirmation() accepts an optional request object (can be None)
#         email_address.send_confirmation(request=None, signup=signup)
#     except EmailAddress.DoesNotExist:
#         # Log or ignore – the email address might have been deleted
#         pass
#     except Exception as exc:
#         # Retry on failure (e.g., SMTP timeout)
#         self.retry(exc=exc, countdown=60)


# accounts/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from allauth.account.models import EmailAddress

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email_task(self, email_address_id, signup=True):
    """
    Send verification email directly, avoiding recursion.
    """
    try:
        email_address = EmailAddress.objects.get(id=email_address_id)
        user = email_address.user

        # Generate the confirmation URL (allauth provides a helper)
        from allauth.account.utils import url_str_to_user_pk
        from allauth.account.views import ConfirmEmailView
        from django.urls import reverse

        # The safest way: use allauth's built‑in confirmation URL generation
        # (requires the key, which is an HMAC)
        from allauth.account.models import EmailConfirmationHMAC
        confirmation = EmailConfirmationHMAC(email_address)
        confirm_url = reverse('account_confirm_email', args=[confirmation.key])
        # Build absolute URL
        site_url = getattr(settings, 'SITE_URL', 'https://omnichannel.autos')
        full_url = f"{site_url}{confirm_url}"

        subject = "Confirm your email address"
        message = f"Hello {user.username},\n\nPlease confirm your email address by clicking the link below:\n\n{full_url}\n\nThank you!"
        html_message = f"<p>Hello {user.username},</p><p>Please confirm your email address by clicking the link below:</p><p><a href='{full_url}'>Confirm email</a></p><p>Thank you!</p>"

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_address.email],
            fail_silently=False,
            html_message=html_message,
        )
    except EmailAddress.DoesNotExist:
        # Do nothing – email address no longer exists
        pass
    except Exception as exc:
        # Retry on any other exception
        raise self.retry(exc=exc)