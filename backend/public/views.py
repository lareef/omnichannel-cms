from django.shortcuts import render, get_object_or_404, redirect, render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from tickets.models import TicketCategory, TicketCategoryField, Message, MessageAttachment
from .forms import PublicSubmissionForm
from .models import PublicTicketSubmission, TicketTrackingToken
from django.contrib import messages
from django.utils import  timezone
import uuid
from django.template.loader import render_to_string


# from django.conf import settings
from tickets.models import Ticket, TicketStatus, TicketPriority, TicketChannel
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

def old_track_ticket(request, token):
    token_obj = get_object_or_404(TicketTrackingToken, token=token, expires_at__gte=timezone.now())
    ticket = token_obj.ticket
    messages_list = ticket.messages.filter(is_internal_note=False).exclude(sender_type='system').order_by('sent_at')
    if request.method == 'POST':
        reply_text = request.POST.get('reply')
        if reply_text:
            Message.objects.create(
                ticket=ticket,
                sender_type='customer',
                sender_name=ticket.customer_name or 'Customer',
                content=reply_text,
                is_internal_note=False
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
def old_track_entry(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        try:
            token_obj = TicketTrackingToken.objects.get(token=token, expires_at__gte=timezone.now())
            return redirect('track_ticket', token=token)
        except TicketTrackingToken.DoesNotExist:
            messages.error(request, "Invalid or expired token.")
    return render(request, 'public/track_entry.html')
def old_submit_complaint(request):
    if request.method == 'POST':
        form = PublicSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            # Gather dynamic fields into extra_data JSON
            dynamic_data = {}
            for key, value in request.POST.items():
                if key.startswith('dynamic_'):
                    field_key = key[8:]  # remove 'dynamic_' prefix
                    dynamic_data[field_key] = value
            submission.extra_data = dynamic_data
            submission.save()
            messages.success(request, "Your complaint has been submitted. You will receive a tracking link shortly.")
            return redirect('track_entry')
    else:
        form = PublicSubmissionForm()
    return render(request, 'public/submit_complaint.html', {'form': form})

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
            default_status = TicketStatus.objects.get(code='OPEN')  # adjust code as needed
            default_priority = TicketPriority.objects.get(level=3)  # e.g., 'Medium'
            web_channel = TicketChannel.objects.get(code='WEB')    # ensure this exists

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

            messages.success(
                request,
                f"Your complaint has been submitted. Your tracking token is: {token.token}"
            )
            # Redirect to the public track page with the token
            return redirect('track_ticket', token=token.token)
    else:
        form = PublicSubmissionForm()
    return render(request, 'public/submit_complaint.html', {'form': form})


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

@require_http_methods(["GET"])
def category_fields(request):
    category_id = request.GET.get('category')
    if not category_id:
        return HttpResponse('')
    category = get_object_or_404(TicketCategory, id=category_id, is_archived=False)
    fields = category.fields.all().order_by('order')
    return render(request, 'public/partials/category_fields.html', {'fields': fields})
