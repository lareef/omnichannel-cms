from django.core.mail import send_mail
from django.conf import settings
from public.models import TicketTrackingToken
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

def send_ticket_confirmation_email(ticket, request=None):
    if not ticket.customer_email:
        return

    # Get domain from request if available, otherwise fallback to settings
    if request:
        domain = request.get_host()
    else:
        domain = getattr(settings, 'SITE_URL', 'omnichannel.autos')

    token_obj, _ = TicketTrackingToken.objects.get_or_create(ticket=ticket)
    tracking_link = f"https://{domain}/track/{token_obj.token}"

    subject = f"Your complaint has been received (Ticket #{ticket.ticket_number})"
    message = (
        f"Dear {ticket.customer_name},\n\n"
        f"Thank you for contacting us. Your complaint has been registered.\n"
        f"Ticket number: {ticket.ticket_number}\n"
        f"Track status: {tracking_link}\n\n"
        f"We will get back to you shortly.\n\n"
        f"Best regards,\nSupport Team"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [ticket.customer_email])

# def send_ticket_confirmation_email(ticket):
#     """
#     Send an email to the customer confirming ticket creation.
#     """
#     if not ticket.customer_email:
#         return

#     # Get or create tracking token
#     token_obj, _ = TicketTrackingToken.objects.get_or_create(ticket=ticket)
#     tracking_link = f"https://{settings.SITE_URL}/track/{token_obj.token}"

#     subject = f"Your complaint has been received (Ticket #{ticket.ticket_number})"
#     message = (
#         f"Dear {ticket.customer_name},\n\n"
#         f"Thank you for contacting us. Your complaint has been registered.\n"
#         f"Ticket number: {ticket.ticket_number}\n"
#         f"Track status: {tracking_link}\n\n"
#         f"We will get back to you shortly.\n\n"
#         f"Best regards,\nSupport Team"
#     )
#     from_email = settings.DEFAULT_FROM_EMAIL
#     recipient_list = [ticket.customer_email]

#     send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    
def send_whatsapp_new_ticket_notification(ticket):
    """
    Send a WhatsApp message to the customer when a new ticket is created via web form.
    """
    if not ticket.customer_contact or not ticket.customer_contact.isdigit():
        return

    customer_name = ticket.customer_name or "Valued Customer"
    ticket_number = ticket.ticket_number

    # Get tracking token
    token_obj, _ = TicketTrackingToken.objects.get_or_create(ticket=ticket)
    tracking_link = f"https://{settings.SITE_URL}/track/{token_obj.token}"

    message = (
        f"🆕 *New Ticket Created*\n\n"
        f"Dear {customer_name},\n\n"
        f"Your complaint has been registered.\n"
        f"Ticket number: {ticket_number}\n"
        f"Track status: {tracking_link}\n\n"
        f"We will get back to you shortly.\n\n"
        f"Best regards,\nSupport Team"
    )

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
            to=f'whatsapp:{ticket.customer_contact}'
        )
        logger.info(f"WhatsApp new ticket notification sent for {ticket.ticket_number}")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp notification: {e}")