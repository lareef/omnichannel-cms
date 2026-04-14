from django.shortcuts import render, get_object_or_404, redirect, render
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods, require_POST
from tickets.models import TicketCategory, TicketCategoryField, Message, MessageAttachment, Ticket, TicketStatus, TicketPriority, TicketChannel
from .forms import PublicSubmissionForm
from .models import PublicTicketSubmission, TicketTrackingToken
from django.contrib import messages
from django.utils import  timezone
import uuid
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from twilio.twiml.messaging_response import MessagingResponse
from customers.models import Customer
from allauth.account.models import EmailAddress
import logging
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from tickets.models import MessageAttachment
from accounts.models import Department  # adjust import if needed
from notifications.views import send_ticket_confirmation_email, send_whatsapp_new_ticket_notification


logger = logging.getLogger(__name__)

def generate_ticket_number():
    """Generate a unique ticket number, e.g., CRM-2025-00001"""
    from django.utils.timezone import now
    year = now().year
    last_ticket = Ticket.objects.filter(ticket_number__startswith=f"CRM-{year}").order_by('ticket_number').last()
    if last_ticket:
        last_num = int(last_ticket.ticket_number.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    return f"CRM-{year}-{new_num:05d}"

@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    try:
        from_number = request.POST.get('From', '').replace('whatsapp:', '')
        message_body = request.POST.get('Body', '').strip()
        if not from_number or not message_body:
            return HttpResponseBadRequest("Missing parameters")

        # Find or create customer
        customer, _ = Customer.objects.get_or_create(
            phone=from_number,
            defaults={'name': f'Customer {from_number}', 'customer_type': 'individual'}
        )

        # Lookup objects (get or create)
        whatsapp_channel, _ = TicketChannel.objects.get_or_create(code='whatsapp', defaults={'name': 'WhatsApp'})
        open_status, _ = TicketStatus.objects.get_or_create(code='open', defaults={'name': 'Open', 'is_closed_state': False})
        medium_priority, _ = TicketPriority.objects.get_or_create(level=3, defaults={'code': 'medium', 'name': 'Medium'})
        default_category, _ = TicketCategory.objects.get_or_create(code='whatsapp', defaults={'name': 'WhatsApp'})
        default_department, _ = Department.objects.get_or_create(code='general', defaults={'name': 'General', 'is_active': True})

        # --- Duplicate prevention: check for existing open ticket ---
        existing_open_ticket = Ticket.objects.filter(
            customer=customer,
            status__is_closed_state=False,
            channel=whatsapp_channel
        ).order_by('-created_at').first()

        # Helper to download and save attachments for a given message
        def save_attachments(message_instance):
            num_media = int(request.POST.get('NumMedia', 0))
            for i in range(num_media):
                media_url = request.POST.get(f'MediaUrl{i}')
                content_type = request.POST.get(f'MediaContentType{i}')
                logger.info(f"MediaUrl{i}: {media_url}, ContentType: {content_type}")
                if media_url:
                    try:
                        # Download media using Twilio credentials for auth (optional but recommended)
                        auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                        resp = requests.get(media_url, auth=auth, timeout=10)
                        logger.info(f"Download status for {i}: {resp.status_code}")
                        if resp.status_code == 200:
                            # Generate a unique filename (e.g., using UUID + extension)
                            import uuid
                            ext = content_type.split('/')[-1] if content_type else 'bin'
                            filename = f"whatsapp_{uuid.uuid4().hex}.{ext}"
                            attachment = MessageAttachment.objects.create(
                                message=message_instance,
                                file=ContentFile(resp.content, name=filename),
                                original_name=f"media_{i}",
                                content_type=content_type,
                                size=len(resp.content),
                            )
                            logger.info(f"Saved attachment {attachment.id} for message {message_instance.id}")
                        else:
                            logger.warning(f"Failed to download media from {media_url}, status {resp.status_code}")
                    except Exception as e:
                        logger.exception(f"Error downloading media: {e}")

        if existing_open_ticket:
            ticket = existing_open_ticket
            # Create a message for the customer's text
            msg = Message.objects.create(
                ticket=ticket,
                sender_type='customer',
                sender_name=customer.name,
                content=message_body,
                is_internal_note=False,
            )
            save_attachments(msg)
            logger.info(f"Appended message to existing ticket {ticket.ticket_number}")
            reply_text = f"Thank you. Your message has been added to ticket #{ticket.ticket_number}."
        else:
            # Create new ticket
            ticket_number = generate_ticket_number()
            ticket = Ticket.objects.create(
                ticket_number=ticket_number,
                customer=customer,
                customer_name=customer.name,
                customer_contact=from_number,
                subject="WhatsApp Message",
                description=message_body,
                channel=whatsapp_channel,
                priority=medium_priority,
                status=open_status,
                category=default_category,
                department=default_department,
                source_system='whatsapp',
            )
            # Also create a Message record for the initial customer message (to attach media)
            msg = Message.objects.create(
                ticket=ticket,
                sender_type='customer',
                sender_name=customer.name,
                content=message_body,
                is_internal_note=False,
            )
            save_attachments(msg)
            logger.info(f"Created new ticket {ticket.ticket_number}")
            # Create tracking token for rich reply
            token_obj, _ = TicketTrackingToken.objects.get_or_create(ticket=ticket)
            tracking_link = f"https://{request.get_host()}/track/{token_obj.token}"
            reply_text = (
                f"Thank you for contacting us. Your complaint has been received.\n"
                f"Ticket number: {ticket.ticket_number}\n"
                f"Track status: {tracking_link}\n"
                f"We will get back to you shortly."
            )

        # Send auto‑reply
        resp = MessagingResponse()
        resp.message(reply_text)
        return HttpResponse(str(resp), content_type='text/xml')

    except Exception as e:
        logger.exception("Error in webhook")
        return HttpResponseBadRequest(str(e))


# @csrf_exempt
# @require_POST
# def whatsapp_webhook(request):
#     try:
#         from_number = request.POST.get('From', '').replace('whatsapp:', '')
#         message_body = request.POST.get('Body', '').strip()
#         if not from_number or not message_body:
#             return HttpResponseBadRequest("Missing parameters")

#         # Find or create customer
#         customer, _ = Customer.objects.get_or_create(
#             phone=from_number,
#             defaults={'name': f'Customer {from_number}', 'customer_type': 'individual'}
#         )

#         # Lookup objects (get or create)
#         whatsapp_channel, _ = TicketChannel.objects.get_or_create(code='whatsapp', defaults={'name': 'WhatsApp'})
#         open_status, _ = TicketStatus.objects.get_or_create(code='open', defaults={'name': 'Open', 'is_closed_state': False})
#         medium_priority, _ = TicketPriority.objects.get_or_create(level=3, defaults={'code': 'medium', 'name': 'Medium'})
#         default_category, _ = TicketCategory.objects.get_or_create(code='whatsapp', defaults={'name': 'WhatsApp'})
#         default_department, _ = Department.objects.get_or_create(code='general', defaults={'name': 'General', 'is_active': True})

#         # --- Duplicate prevention: check for existing open ticket ---
#         existing_open_ticket = Ticket.objects.filter(
#             customer=customer,
#             status__is_closed_state=False,
#             channel=whatsapp_channel
#         ).order_by('-created_at').first()

#         if existing_open_ticket:
#             ticket = existing_open_ticket
#             # Append message as a new customer message
#             Message.objects.create(
#                 ticket=ticket,
#                 sender_type='customer',
#                 sender_name=customer.name,
#                 content=message_body,
#                 is_internal_note=False,
#             )
#             logger.info(f"Appended message to existing ticket {ticket.ticket_number}")
#             # Optionally, send a different auto‑reply (e.g., "Message added to your existing ticket")
#             reply_text = f"Thank you. Your message has been added to ticket #{ticket.ticket_number}."
#         else:
#             # Create new ticket
#             ticket_number = generate_ticket_number()
#             ticket = Ticket.objects.create(
#                 ticket_number=ticket_number,
#                 customer=customer,
#                 customer_name=customer.name,
#                 customer_contact=from_number,
#                 subject="WhatsApp Message",
#                 description=message_body,
#                 channel=whatsapp_channel,
#                 priority=medium_priority,
#                 status=open_status,
#                 category=default_category,
#                 department=default_department,
#                 source_system='whatsapp',
#             )
#             logger.info(f"Created new ticket {ticket.ticket_number}")
#             # Create tracking token for rich reply
#             token_obj, _ = TicketTrackingToken.objects.get_or_create(ticket=ticket)
#             tracking_link = f"https://{request.get_host()}/track/{token_obj.token}"
#             reply_text = (
#                 f"Thank you for contacting us. Your complaint has been received.\n"
#                 f"Ticket number: {ticket.ticket_number}\n"
#                 f"Track status: {tracking_link}\n"
#                 f"We will get back to you shortly."
#             )

#         # Send auto‑reply
#         resp = MessagingResponse()
#         resp.message(reply_text)
#         return HttpResponse(str(resp), content_type='text/xml')

#     except Exception as e:
#         logger.exception("Error in webhook")
#         return HttpResponseBadRequest(str(e))
    
def home(request):
    pass
    return render(request, 'public/landing.html')

def track_ticket(request, token):
    token_obj = get_object_or_404(TicketTrackingToken, token=token, expires_at__gte=timezone.now())
    ticket = token_obj.ticket
    message_list = ticket.messages.filter(is_internal_note=False).exclude(sender_type='system').order_by('sent_at')

    if request.method == 'POST':
        reply_text = request.POST.get('reply')
        if reply_text:
            # Create the message
            message = Message.objects.create(
                ticket=ticket,
                sender_type='customer',
                sender_name=ticket.customer_name or 'Customer',
                content=reply_text,
                is_internal_note=False
            )
            # Handle file uploads
            files = request.FILES.getlist('attachments')
            for f in files:
                if f.size > 10 * 1024 * 1024:  # 10 MB limit
                    messages.warning(request, f"File {f.name} exceeds 10MB and was not uploaded.")
                    continue
                MessageAttachment.objects.create(
                    message=message,
                    file=f,
                    original_name=f.name,
                    content_type=f.content_type,
                    size=f.size
                )

            # If this is an HTMX request, return the new message HTML
            if getattr(request, 'htmx', False):
                html = render_to_string('public/partials/single_message.html', {'message': message}, request=request)
                return HttpResponse(html)
            else:
                # Non‑HTMX fallback: full redirect
                messages.success(request, "Your reply has been added.")
                return redirect('track_ticket', token=token)
        else:
            # Empty reply – you could return an error partial, but for simplicity we redirect back with error
            if getattr(request, 'htmx', False):
                return HttpResponse("Reply cannot be empty.", status=400)
            else:
                messages.error(request, "Reply cannot be empty.")
                return redirect('track_ticket', token=token)

    context = {
        'ticket': ticket,
        'messages': message_list,
        'token': token,
    }
    return render(request, 'public/track_ticket.html', context)

def track_ticket_no_htmx(request, token):
    token_obj = get_object_or_404(TicketTrackingToken, token=token, expires_at__gte=timezone.now())
    ticket = token_obj.ticket
    messages_list = ticket.messages.filter(is_internal_note=False).exclude(sender_type='system').order_by('sent_at')  # exclude internal notes & system messages for public

    if request.method == 'POST':
        reply_text = request.POST.get('reply')
        if reply_text:
            # Create the message
            message = Message.objects.create(
                ticket=ticket,
                sender_type='customer',
                sender_name=ticket.customer_name or 'Customer',
                content=reply_text,
                is_internal_note=False
            )
            # Handle file uploads
            files = request.FILES.getlist('attachments')
            for f in files:
                # Basic validation (you can add more checks)
                if f.size > 10 * 1024 * 1024:  # 10MB limit
                    messages.warning(request, f"File {f.name} exceeds 10MB and was not uploaded.")
                    continue
                MessageAttachment.objects.create(
                    message=message,
                    file=f,
                    original_name=f.name,
                    content_type=f.content_type,
                    size=f.size
                )
            messages.success(request, "Your reply has been added.")
        return redirect('track_ticket', token=token)

    context = {
        'ticket': ticket,
        'messages': messages_list,
        'token': token,
    }
    return render(request, 'public/track_ticket.html', context)

def track_entry(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        ticket_number = request.POST.get('ticket_number')
        contact = request.POST.get('contact')

        # Method 1: Token
        if token:
            try:
                token_obj = TicketTrackingToken.objects.get(token=token, expires_at__gte=timezone.now())
                return redirect('track_ticket', token=token_obj.token)
            except TicketTrackingToken.DoesNotExist:
                messages.error(request, "Invalid or expired token.")
                return render(request, 'public/partials/track_entry.html')

        # Method 2: Ticket number + contact
        elif ticket_number and contact:
            try:
                ticket = Ticket.objects.get(ticket_number=ticket_number)
                # Check contact matches either customer_email or customer_contact
                if (ticket.customer_email == contact) or (ticket.customer_contact == contact):
                    # Optionally create a token on‑the‑fly for redirection
                    token_obj, created = TicketTrackingToken.objects.get_or_create(
                        ticket=ticket,
                        defaults={'expires_at': timezone.now() + timezone.timedelta(days=30)}
                    )
                    return redirect('track_ticket', token=token_obj.token)
                else:
                    messages.error(request, "Ticket number and contact do not match.")
            except Ticket.DoesNotExist:
                messages.error(request, "Ticket number not found.")
        else:
            messages.error(request, "Please provide either a token OR ticket number + contact.")

    return render(request, 'public/partials/track_entry.html')

def submit_complaint(request):
    if request.method == 'POST':
        form = PublicSubmissionForm(request.POST)
        if form.is_valid():
            # 1. Save the submission (optional, for auditing)
            submission = form.save(commit=False)
            dynamic_data = {}
            for key, value in request.POST.items():
                if key.startswith('dynamic_'):
                    field_key = key[8:]  # remove 'dynamic_' prefix
                    dynamic_data[field_key] = value
            submission.extra_data = dynamic_data
            submission.save()

            # 2. Create the actual Ticket
            #    You need to define default status, priority, channel, etc.
            default_status = TicketStatus.objects.get(code='open')  # adjust code as needed
            default_priority = TicketPriority.objects.get(level=3)  # e.g., 'Medium'
            web_channel = TicketChannel.objects.get(code='web')    # ensure this exists

            ticket = Ticket.objects.create(
                ticket_number=generate_ticket_number(),  # implement this function
                uuid=uuid.uuid4(),
                customer_name=submission.customer_name,
                customer_contact=submission.contact,
                customer_email=submission.contact if '@' in submission.contact else '',
                subject=f"Complaint via web: {submission.category.name}",
                description=submission.description,
                channel=web_channel,
                category=submission.category,
                priority=default_priority,
                status=default_status,
                extra_data=submission.extra_data,
                # Set department from category if needed
                department=submission.category.department,
                # created_by remains null for public submissions
            )

            # 3. Create a tracking token
            token = TicketTrackingToken.objects.create(
                ticket=ticket,
                expires_at=timezone.now() + timezone.timedelta(days=30)  # e.g., 30 days
            )

            # 4. (Optional) Send email/SMS with tracking link
            # send_tracking_notification(ticket, token)
            
            # In public/views.py, after ticket creation
            if '@' in submission.contact:   # email
                send_ticket_confirmation_email(ticket, request)
            elif submission.contact.isdigit():   # phone number (basic check)
                send_whatsapp_new_ticket_notification(ticket)

            messages.success(
                request,
                f"Your complaint has been submitted. Your tracking token is: {token.token}"
            )
            # Redirect to the public track page with the token
            return redirect('track_ticket', token=token.token)
    else:
        form = PublicSubmissionForm()
    return render(request, 'public/submit_complaint.html', {'form': form})



@require_http_methods(["GET"])
def category_fields(request):
    category_id = request.GET.get('category')
    if not category_id:
        return HttpResponse('')
    category = get_object_or_404(TicketCategory, id=category_id, is_archived=False)
    fields = category.fields.all().order_by('order')
    return render(request, 'public/partials/category_fields.html', {'fields': fields})
