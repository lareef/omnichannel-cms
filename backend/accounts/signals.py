from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from django.core.mail import send_mail

# @receiver(user_signed_up)
def send_verification_email(sender, request, user, **kwargs):
    # Generate a verification link (you need to create a view)
    # For simplicity, you can resend the allauth confirmation using the method below
    from allauth.account.models import EmailAddress
    email_address = EmailAddress.objects.get(user=user, primary=True)
    email_address.send_confirmation(request, signup=True)