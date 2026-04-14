from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.urls import reverse, reverse_lazy
from .models import Ticket, TicketUpdate, Message, MessageAttachment, TicketEscalation, EscalationPolicy, EscalationTarget
from .forms import TicketFilterForm, TicketUpdateForm, MessageForm, EscalationPolicyForm
from django.http import HttpResponseForbidden, HttpResponse
from accounts.decorators import role_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, View, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils import timezone
from notifications.utils import notify_ticket_update
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.admin.views.decorators import staff_member_required
from twilio.rest import Client
from django.conf import settings
import logging
from twilio.base.exceptions import TwilioRestException
from django.core.mail import send_mail
from utilities.models import WhatsAppTemplate

from django.template import Template, Context
from django.utils.safestring import mark_safe


def send_whatsapp_message(ticket, comment, agent_user):
    # Get active template
    template_obj = WhatsAppTemplate.objects.filter(is_active=True).first()
    if not template_obj:
        template_obj = WhatsAppTemplate.objects.create(
            name="default",
            header="Dear {{customer_name}},",
            footer="Best regards,\n{{agent_name}}\nSupport Team",
            separator="\n\n",
            is_active=True
        )

    # Replace any literal \n with actual newlines (in case admin typed them)
    header = template_obj.header.replace('\\n', '\n')
    footer = template_obj.footer.replace('\\n', '\n')
    separator = template_obj.separator.replace('\\n', '\n')

    context = {
        'customer_name': ticket.customer_name or "Valued Customer",
        'agent_name': agent_user.get_full_name() or agent_user.username,
        'comment': comment,
        'ticket_number': ticket.ticket_number,
    }

    from django.template import Template, Context
    header_rendered = Template(header).render(Context(context))
    footer_rendered = Template(footer).render(Context(context))

    full_message = f"{header_rendered}{separator}{comment}{separator}{footer_rendered}"

    # Send via Twilio
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=full_message,
        from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
        to=f'whatsapp:{ticket.customer_contact}'
    )

def send_status_update_via_whatsapp(ticket, old_status, new_status, agent_user=None):
    """
    Send a WhatsApp message to the customer informing them of a status change.
    """
    if not ticket.customer_contact:
        return

    customer_name = ticket.customer_name or "Valued Customer"
    agent_name = agent_user.get_full_name() if agent_user else "System"

    if new_status.is_closed_state:
        status_text = "closed"
        additional = "Thank you for your patience. If you have further questions, please reply to this message."
    else:
        status_text = f"updated to {new_status.name}"
        additional = "We will continue working on your request."

    message = (
        f"🔔 *Ticket #{ticket.ticket_number} Status Update*\n\n"
        f"Dear {customer_name},\n\n"
        f"Your ticket status has been {status_text}.\n"
        f"{additional}\n\n"
        f"Best regards,\n{agent_name}\nSupport Team"
    )

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
            to=f'whatsapp:{ticket.customer_contact}'
        )
        logger.info(f"Status update WhatsApp sent for ticket {ticket.ticket_number}")
    except Exception as e:
        logger.error(f"Failed to send status update WhatsApp: {e}")

# def send_whatsapp_message(ticket, comment, agent_user):
#     """
#     Send a WhatsApp reply using the active template.
#     """
#     # Get active template (first active, or create default if none)
#     template_obj = WhatsAppTemplate.objects.filter(is_active=True).first()
#     if not template_obj:
#         # Create a default template on the fly (optional)
#         template_obj = WhatsAppTemplate.objects.create(
#             name="default",
#             header="Dear {{customer_name}},",
#             footer="Best regards,\n{{agent_name}}\nSupport Team",
#             separator="\n\n",
#             is_active=True
#         )

#     # Prepare context
#     context = {
#         'customer_name': ticket.customer_name or "Valued Customer",
#         'agent_name': agent_user.get_full_name() or agent_user.username,
#         'comment': comment,
#         'ticket_number': ticket.ticket_number,
#         'company_name': settings.COMPANY_NAME,  # optional, add to settings
#         'website': settings.COMPANY_WEBSITE,    # optional
#     }

#     # Build the full message
#     header = Template(template_obj.header).render(Context(context))
#     footer = Template(template_obj.footer).render(Context(context))
#     separator = template_obj.separator

#     full_message = f"{header}{separator}{comment}{separator}{footer}"

#     # Optional: add a link to the logo (if you have a public URL)
#     # full_message += f"\n\n{settings.COMPANY_LOGO_URL}"  # text link

#     try:
#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#         message = client.messages.create(
#             body=full_message,
#             from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
#             to=f'whatsapp:{ticket.customer_contact}'
#         )
#         logger.info(f"WhatsApp message sent. SID: {message.sid}")
#         return True
#     except Exception as e:
#         logger.error(f"Twilio error: {e}")
#         return False



class AgentRequiredMixin(UserPassesTestMixin):
    """Allow only users with a valid agent/supervisor/admin role."""
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        # Must have a role and the role code must be in allowed list
        if not user.role:
            return False
        return user.role.code in ['agent', 'supervisor', 'admin', 'manager']

    def handle_no_permission(self):
        user = self.request.user
        if user.is_authenticated and not user.role:
            # Authenticated but no role – show a custom message
            return render(
                self.request,
                'tickets/role_required_error.html',
                status=403
            )
        # For all other cases (not authenticated, or other reasons), raise 403
        raise PermissionDenied
class SupervisorRequiredMixin(UserPassesTestMixin):
    """Allow only supervisors and admins."""
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role and user.role.code in ['supervisor', 'admin', 'manager']
    
class ManagerRequiredMixin(UserPassesTestMixin):
    """Allow only managers and admins."""
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role and user.role.code in ['manager', 'admin']

class DashboardView(LoginRequiredMixin, AgentRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/dashboard.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        # Base queryset with role filtering
        base_queryset = Ticket.objects.select_related(
            'status', 'priority', 'customer', 'assigned_to'
        ).order_by('-created_at')

        user = self.request.user
        if user.role and user.role.code == 'agent':
            base_queryset = base_queryset.filter(
                Q(assigned_to=user) |
                Q(assigned_to__isnull=True, department=user.department)
            )

        self.base_queryset = base_queryset   # store for stats

        # Now apply custom card filters (optional)
        queryset = base_queryset
        if self.request.GET.get('open') == '1':
            queryset = queryset.filter(status__is_closed_state=False)
        if self.request.GET.get('overdue_response') == '1':
            now = timezone.now()
            queryset = queryset.filter(
                response_due_at__lt=now,
                first_response_at__isnull=True
            )

        # Apply filter form (assignment, status, priority, search)
        self.filter_form = TicketFilterForm(self.request.GET, queryset=queryset)
        self.filter_form.set_user(user)
        if self.filter_form.is_valid():
            queryset = self.filter_form.filter_queryset(queryset)

        self.filtered_queryset = queryset
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Use the already filtered queryset for stats (self.filtered_queryset)
        # base_queryset = self.filtered_queryset

        context['open_tickets_count'] = self.base_queryset.filter(status__is_closed_state=False).count()
        context['unassigned_count'] = self.base_queryset.filter(assigned_to__isnull=True).count()
        context['overdue_response_count'] = self.base_queryset.filter(
            response_due_at__lt=timezone.now(),
            first_response_at__isnull=True
        ).count()
        context['my_tickets_count'] = self.base_queryset.filter(assigned_to=user).count()
        context['filter_form'] = self.filter_form
        return context

# Simple ticket list view (same as dashboard but without the dashboard-specific UI)
class TicketListView(DashboardView):
    template_name = 'tickets/partials/ticket_list.html'


# ----- Ticket Detail -----
class TicketDetailView(LoginRequiredMixin, AgentRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/partials/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        # Ensure user has permission to view this ticket
        qs = super().get_queryset()
        user = self.request.user
        if user.role and user.role.code == 'agent':
            qs = qs.filter(
                Q(assigned_to=user) |
                Q(assigned_to__isnull=True, department=user.department)
            )
        return qs        # ... existing permission logic ...

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.object
        # Prefetch messages and their attachments to avoid N+1 queries
        context['messages'] = ticket.messages.select_related('sender_user').prefetch_related('attachments').order_by('sent_at')
        context['updates'] = ticket.updates.select_related('updated_by').order_by('-created_at')[:20]
        context['message_form'] = MessageForm()
        context['update_form'] = TicketUpdateForm(instance=ticket)

        return context

class old_TicketDetailView(LoginRequiredMixin, AgentRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        # Ensure user has permission to view this ticket
        qs = super().get_queryset()
        user = self.request.user
        if user.role and user.role.code == 'agent':
            qs = qs.filter(
                Q(assigned_to=user) |
                Q(assigned_to__isnull=True, department=user.department)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.object
        context['messages'] = ticket.messages.select_related('sender_user').order_by('sent_at')
        context['updates'] = ticket.updates.select_related('updated_by').order_by('-created_at')[:20]
        context['message_form'] = MessageForm()
        context['update_form'] = TicketUpdateForm(instance=ticket)
        return context

logger = logging.getLogger(__name__)


@login_required
def send_whatsapp_reply(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    # Optional: check user role (agent, supervisor, admin)
    if request.method == 'POST':
        reply_body = request.POST.get('reply')
        if not reply_body:
            messages.error(request, "Reply text is empty.")
            return redirect('tickets:ticket_detail', pk=ticket.pk)

        if not ticket.customer_contact:
            messages.error(request, "Customer contact number missing.")
            return redirect('tickets:ticket_detail', pk=ticket.pk)

        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=reply_body,
                from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
                to=f'whatsapp:{ticket.customer_contact}'
            )
            # Save agent's message as a conversation entry
            Message.objects.create(
                ticket=ticket,
                sender_type='agent',
                sender_user=request.user,
                content=reply_body,
                is_internal_note=False,
            )
            messages.success(request, f"WhatsApp reply sent. SID: {message.sid}")
            logger.info(f"WhatsApp reply sent to {ticket.customer_contact}")
        except TwilioRestException as e:
            logger.error(f"Twilio error: {e}")
            messages.error(request, f"Twilio error: {e}")
        except Exception as e:
            logger.exception("Unexpected error")
            messages.error(request, f"Failed to send reply: {str(e)}")
        return redirect('tickets:ticket_detail', pk=ticket.pk)
    return redirect('tickets:ticket_detail', pk=ticket.pk)

# @staff_member_required
# def send_whatsapp_reply(request, pk):
#     ticket = get_object_or_404(Ticket, pk=pk)
#     if request.method == 'POST':
#         reply_body = request.POST.get('reply')
#         if reply_body and ticket.customer_contact:
#             # Send via Twilio
#             client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#             client.messages.create(
#                 body=reply_body,
#                 from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
#                 to=f'whatsapp:{ticket.customer_contact}'
#             )
#             # Save agent's message as a message record (optional)
#             Message.objects.create(
#                 ticket=ticket,
#                 sender_type='agent',
#                 sender_user=request.user,
#                 content=reply_body,
#                 is_internal_note=False,
#             )
#             messages.success(request, "WhatsApp reply sent.")
#         else:
#             messages.error(request, "Missing reply text or customer contact.")
#         return redirect('tickets:ticket_detail', pk=ticket.pk)
#     return redirect('tickets:ticket_detail', pk=ticket.pk)
# ----- HTMX Partials -----

def ticket_detail_partial(request, pk):
    """Return ticket detail snippet for modal."""
    ticket = get_object_or_404(Ticket, pk=pk)
    # Permission check
    user = request.user
    if user.role and user.role.code == 'agent' and not (ticket.assigned_to == user or (ticket.assigned_to is None and ticket.department == user.department)):
        return HttpResponseForbidden()

    # messages_qs = ticket.messages.select_related('sender_user').prefetch_related('attachments').order_by('sent_at')
    context = {
        # 'ticket': ticket,
        # 'messages': messages_qs,
        'ticket': ticket,
        'messages': ticket.messages.select_related('sender_user').prefetch_related('attachments').order_by('sent_at'),
        'updates': ticket.updates.select_related('updated_by').order_by('-created_at')[:20],
        'message_form': MessageForm(),
        'update_form': TicketUpdateForm(instance=ticket),
    }
    html = render_to_string('tickets/partials/ticket_detail.html', context, request=request)
    return HttpResponse(html)

# def send_whatsapp_message(to_number, message_body):
#     try:
#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#         message = client.messages.create(
#             body=message_body,
#             from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
#             to=f'whatsapp:{to_number}'
#         )
#         logger.info(f"WhatsApp message sent. SID: {message.sid}")
#         return True
#     except TwilioRestException as e:
#         logger.error(f"Twilio error: {e}")
#         return False
#     except Exception as e:
#         logger.exception("Unexpected error sending WhatsApp message")
#         return False

def send_email_reply(ticket, comment, agent_user):
    """Send an email reply to the customer."""
    subject = f"Re: {ticket.subject} (Ticket #{ticket.ticket_number})"
    message = f"Dear {ticket.customer_name},\n\n{comment}\n\n---\nYou can view your ticket at: https://{settings.SITE_DOMAIN}/track/{ticket.tracking_token.token}\n\nThank you."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [ticket.customer_email]

    # Generate a custom Message-ID that includes the ticket ID for threading
    message_id = f"<ticket-{ticket.id}.{timezone.now().timestamp()}@omnichannel.autos>"

    # In-Reply-To can be set if you store the original Message-ID from customer's first email
    # For simplicity, we'll just set a unique Message-ID.

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
        headers={'Message-ID': message_id}
    )

@login_required
def update_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    # Permission check (same as before)
    user = request.user
    # if user.role.code == 'agent' and not (ticket.assigned_to == user or (ticket.assigned_to is None and ticket.department == user.department)):
    if user.role.code == 'agent' and not (ticket.assigned_to == user or (ticket.assigned_to is None )):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = TicketUpdateForm(request.POST, instance=ticket, user=user)
        if form.is_valid():
            # Save ticket changes (status, priority, assigned_to)
            ticket, changes = form.save(updated_by=user)
            # Handle comment
            comment = form.cleaned_data.get('comment')
            is_internal = form.cleaned_data.get('is_internal_note', False)
            if comment:
                # Save as Message
                message = Message.objects.create(
                    ticket=ticket,
                    sender_type='agent',
                    sender_user=user,
                    content=comment,
                    is_internal_note=is_internal,
                )
                
                # Handle attachments
                attachments = request.FILES.getlist('attachments')
                for f in attachments:
                    MessageAttachment.objects.create(
                        message=message,
                        file=f,
                        original_name=f.name,
                        content_type=f.content_type,
                        size=f.size
                    )
                # If channel is WhatsApp and not internal, send WhatsApp reply
                if ticket.channel.code == 'whatsapp' and not is_internal and ticket.customer_contact:
                    send_whatsapp_message(ticket, comment, user)
                # If channel is email and not internal, send email reply
                elif ticket.channel.code == 'email' and not is_internal and ticket.customer_email:
                    send_email_reply(ticket, comment, user)  # define this function (see previous answer)
            # Notify about changes (if any)
            if changes:
                notify_ticket_update(ticket, changes, updated_by=user)
                # Inside update_ticket, after form.save() and before returning response
                if 'old_status' in changes and changes['new_status']:
                    old_status = changes['old_status']
                    new_status = changes['new_status']
                    # Only send if the status changed (not the same) and ticket is WhatsApp
                    if ticket.channel.code == 'whatsapp' and old_status != new_status:
                        send_status_update_via_whatsapp(ticket, old_status, new_status, user)

            # Return updated detail partial (HTMX)
            html = render_to_string('tickets/partials/ticket_detail.html', {'ticket': ticket}, request=request)
            return HttpResponse(html)
        else:
            html = render_to_string('tickets/partials/update_form.html', {'form': form, 'ticket': ticket}, request=request)
            return HttpResponse(html, status=400)
    else:
        form = TicketUpdateForm(instance=ticket, user=user)
        return render(request, 'tickets/partials/update_form.html', {'form': form, 'ticket': ticket})


# def update_ticket(request, pk):
#     ticket = get_object_or_404(Ticket, pk=pk)
#     # Permission check (as before)
#     user = request.user
#     if user.role and user.role.code == 'agent' and not (ticket.assigned_to == user or (ticket.assigned_to is None and ticket.department == user.department)):
#         return HttpResponseForbidden()

#     if request.method == 'POST':
#         form = TicketUpdateForm(request.POST, instance=ticket, user=user)  # pass user
#         if form.is_valid():
#             ticket, changes = form.save(updated_by=user)
#             # Create notifications
#             if changes:
#                 notify_ticket_update(ticket, changes, updated_by=request.user)
#             messages.success(request, "Ticket updated successfully.")
#             # Return updated detail partial
#             messages_qs = ticket.messages.select_related('sender_user').prefetch_related('attachments').order_by('sent_at')
#             context = {
#                 'ticket': ticket,
#                 'messages': messages_qs,
#             }
#             html = render_to_string('tickets/partials/ticket_detail.html', context, request=request)
#             # return HttpResponse(html)
#             response = HttpResponse(html)
#             response['HX-Trigger'] = '{"showToast": {"message": "Ticket updated successfully", "type": "success"}}'
#             return response
#         else:
#             html = render_to_string('tickets/partials/update_form.html', {'form': form, 'ticket': ticket}, request=request)
#             return HttpResponse(html, status=400)
#     else:
#         form = TicketUpdateForm(instance=ticket, user=user)  # pass user
#         return render(request, 'tickets/partials/update_form.html', {'form': form, 'ticket': ticket})
    
def old_update_ticket(request, pk):
    """Handle ticket update form submission (HTMX)."""
    ticket = get_object_or_404(Ticket, pk=pk)
    # Permission check
    user = request.user
    if user.role and user.role.code == 'agent' and not (ticket.assigned_to == user or (ticket.assigned_to is None and ticket.department == user.department)):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = TicketUpdateForm(request.POST, instance=ticket)
        if form.is_valid():
            # Save with user info
            form.save(updated_by=user)
            messages.success(request, "Ticket updated successfully.")
            # Return the updated ticket detail partial (to refresh modal)
            html = render_to_string('tickets/partials/ticket_detail.html', {'ticket': ticket}, request=request)
            return HttpResponse(html)
        else:
            # Return form with errors
            html = render_to_string('tickets/partials/update_form.html', {'form': form, 'ticket': ticket}, request=request)
            return HttpResponse(html, status=400)
    else:
        form = TicketUpdateForm(instance=ticket)
        return render(request, 'tickets/partials/update_form.html', {'form': form, 'ticket': ticket})


def add_message(request, pk):
    """Add a new message (internal note or public reply) via HTMX."""
    ticket = get_object_or_404(Ticket, pk=pk)
    # Permission check
    user = request.user
    if user.role and user.role.code == 'agent' and not (ticket.assigned_to == user or (ticket.assigned_to is None and ticket.department == user.department)):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.ticket = ticket
            message.sender_type = 'agent'
            message.sender_user = user
            message.sender_name = user.get_full_name() or user.username
            message.save()
            # Return the new message HTML to append to list
            html = render_to_string('tickets/partials/single_message.html', {'message': message}, request=request)
            return HttpResponse(html)
        else:
            return HttpResponse("Error", status=400)
    return HttpResponse(status=405)

def add_message_with_attachments(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    # Permission check (as before)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.ticket = ticket
            message.sender_type = 'agent'
            message.sender_user = request.user
            message.sender_name = request.user.get_full_name() or request.user.username
            message.save()

            # Handle uploaded files
            files = request.FILES.getlist('attachments')
            for f in files:
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

            if getattr(request, 'htmx', False):
                html = render_to_string('tickets/partials/single_message.html', {'message': message}, request=request)
                return HttpResponse(html)
            else:
                return redirect('tickets:ticket_detail', pk=ticket.pk)
    return HttpResponse(status=405)

def message_list_partial(request, pk):
    """Return all messages for a ticket (for refreshing)."""
    ticket = get_object_or_404(Ticket, pk=pk)
    messages_qs = ticket.messages.select_related('sender_user').order_by('sent_at')
    html = render_to_string('tickets/partials/message_list.html', {'messages': messages_qs}, request=request)
    return HttpResponse(html)


def update_list_partial(request, pk):
    """Return recent updates for a ticket."""
    ticket = get_object_or_404(Ticket, pk=pk)
    updates = ticket.updates.select_related('updated_by').order_by('-created_at')[:20]
    html = render_to_string('tickets/partials/update_list.html', {'updates': updates}, request=request)
    return HttpResponse(html)

class EscalationListView(SupervisorRequiredMixin, ListView):
    model = TicketEscalation
    template_name = 'tickets/escalation_list.html'
    context_object_name = 'escalations'
    paginate_by = 50
    ordering = ['-escalated_at']


# ----- Escalation Policy Management Views (for supervisors/admins) -----

class EscalationPolicyListView(SupervisorRequiredMixin, ListView):
    model = EscalationPolicy
    template_name = 'tickets/escalation_policy_list.html'
    context_object_name = 'policies'
    paginate_by = 20
    ordering = ['level', 'name']


class EscalationPolicyCreateView(SupervisorRequiredMixin, SuccessMessageMixin, CreateView):
    model = EscalationPolicy
    form_class = EscalationPolicyForm
    template_name = 'tickets/escalation_policy_form.html'
    success_url = reverse_lazy('tickets:escalation_policy_list')
    success_message = "Escalation policy '%(name)s' created successfully."


class EscalationPolicyUpdateView(SupervisorRequiredMixin, SuccessMessageMixin, UpdateView):
    model = EscalationPolicy
    form_class = EscalationPolicyForm
    template_name = 'tickets/escalation_policy_form.html'
    success_url = reverse_lazy('tickets:escalation_policy_list')
    success_message = "Escalation policy '%(name)s' updated successfully."


class EscalationPolicyDeleteView(SupervisorRequiredMixin, DeleteView):
    model = EscalationPolicy
    template_name = 'tickets/escalation_policy_confirm_delete.html'
    success_url = reverse_lazy('tickets:escalation_policy_list')
    success_message = "Escalation policy deleted."

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

# class EscalationPolicyListView(SupervisorRequiredMixin, ListView):
#     """List all escalation policies."""
#     model = EscalationPolicy
#     template_name = 'tickets/escalation_policy_list.html'
#     context_object_name = 'policies'
#     paginate_by = 20
#     ordering = ['level', 'name']
    
#     def get_queryset(self):
#         return super().get_queryset().select_related('sla_rule', 'sla_rule__priority', 'sla_rule__department')


# class EscalationPolicyCreateView(SupervisorRequiredMixin, CreateView):
#     """Create a new escalation policy."""
#     model = EscalationPolicy
#     template_name = 'tickets/escalation_policy_form.html'
#     fields = ['name', 'sla_rule', 'trigger_event', 'threshold_minutes', 'level', 'is_active']
    
#     def get_success_url(self):
#         return reverse('tickets:escalation_policy_list')
    
#     def form_valid(self, form):
#         messages.success(self.request, 'Escalation policy created successfully.')
#         return super().form_valid(form)


# class EscalationPolicyUpdateView(SupervisorRequiredMixin, UpdateView):
#     """Edit an existing escalation policy."""
#     model = EscalationPolicy
#     template_name = 'tickets/escalation_policy_form.html'
#     fields = ['name', 'sla_rule', 'trigger_event', 'threshold_minutes', 'level', 'is_active']
    
#     def get_success_url(self):
#         return reverse('tickets:escalation_policy_list')
    
#     def form_valid(self, form):
#         messages.success(self.request, 'Escalation policy updated successfully.')
#         return super().form_valid(form)


# class EscalationPolicyDeleteView(SupervisorRequiredMixin, DeleteView):
#     """Delete an escalation policy."""
#     model = EscalationPolicy
#     template_name = 'tickets/escalation_policy_confirm_delete.html'
    
#     def get_success_url(self):
#         return reverse('tickets:escalation_policy_list')
    
#     def delete(self, request, *args, **kwargs):
#         messages.success(request, 'Escalation policy deleted successfully.')
#         return super().delete(request, *args, **kwargs)


class EscalationTargetListView(SupervisorRequiredMixin, ListView):
    """List targets for a specific policy."""
    model = EscalationTarget
    template_name = 'tickets/escalation_target_list.html'
    context_object_name = 'targets'
    
    def get_queryset(self):
        policy_id = self.kwargs['pk']
        return EscalationTarget.objects.filter(policy_id=policy_id).select_related(
            'escalate_to_user', 'escalate_to_role', 'escalate_to_department'
        ).order_by('order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['policy'] = get_object_or_404(EscalationPolicy, pk=self.kwargs['pk'])
        return context


class EscalationTargetCreateView(SupervisorRequiredMixin, CreateView):
    """Create a new target for a policy."""
    model = EscalationTarget
    template_name = 'tickets/escalation_target_form.html'
    fields = ['order', 'escalate_to_user', 'escalate_to_role', 'escalate_to_department', 'notification_template']
    
    def form_valid(self, form):
        policy_id = self.kwargs['policy_id']
        form.instance.policy = get_object_or_404(EscalationPolicy, pk=policy_id)
        messages.success(self.request, 'Escalation target added successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('tickets:escalation_target_list', kwargs={'pk': self.kwargs['policy_id']})


class EscalationTargetUpdateView(SupervisorRequiredMixin, UpdateView):
    """Edit an existing escalation target."""
    model = EscalationTarget
    template_name = 'tickets/escalation_target_form.html'
    fields = ['order', 'escalate_to_user', 'escalate_to_role', 'escalate_to_department', 'notification_template']
    
    def get_success_url(self):
        return reverse('tickets:escalation_target_list', kwargs={'pk': self.object.policy_id})
    
    def form_valid(self, form):
        messages.success(self.request, 'Escalation target updated successfully.')
        return super().form_valid(form)


class EscalationTargetDeleteView(SupervisorRequiredMixin, DeleteView):
    """Delete an escalation target."""
    model = EscalationTarget
    template_name = 'tickets/escalation_target_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('tickets:escalation_target_list', kwargs={'pk': self.object.policy_id})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Escalation target deleted successfully.')
        return super().delete(request, *args, **kwargs)

# @login_required
# @role_required(['agent', 'supervisor', 'admin'])

# def update_ticket(request, pk):
#     ticket = get_object_or_404(Ticket, pk=pk)
#     if request.method == 'POST':
#         form = TicketUpdateForm(request.POST, instance=ticket)
#         if form.is_valid():
#             # Save changes, create TicketUpdate record
#             form.save(updated_by=request.user)
#             messages.success(request, "Ticket updated.")
#             return HttpResponse(status=204)  # No content – HTX will refresh detail
#     else:
#         form = TicketUpdateForm(instance=ticket)
#     return render(request, 'tickets/partials/update_form.html', {'form': form, 'ticket': ticket})

# @login_required
# def dashboard(request):
#     # Base queryset: tickets assigned to current user, or all if supervisor
#     if request.user.role and request.user.role.code in ['supervisor', 'admin']:
#         tickets = Ticket.objects.all()
#     else:
#         tickets = Ticket.objects.filter(assigned_to=request.user)
    
#     # Apply filters (status, priority, etc.) – we'll use a form
#     form = TicketFilterForm(request.GET)
#     if form.is_valid():
#         if form.cleaned_data.get('status'):
#             tickets = tickets.filter(status=form.cleaned_data['status'])
#         if form.cleaned_data.get('priority'):
#             tickets = tickets.filter(priority=form.cleaned_data['priority'])
#         # etc.

#     context = {
#         'tickets': tickets.select_related('status', 'priority', 'customer'),
#         'filter_form': form,
#     }
#     return render(request, 'tickets/dashboard.html', context)

# @login_required
# def ticket_detail_partial(request, pk):
#     ticket = get_object_or_404(Ticket, pk=pk)
#     # Check permission: assigned agent or supervisor
#     if not (request.user == ticket.assigned_to or (request.user.role and request.user.role.code in ['supervisor', 'admin'])):
#         return HttpResponseForbidden()
#     updates = ticket.updates.all().order_by('-created_at')[:10]
#     messages = ticket.messages.all().order_by('-sent_at')[:20]
#     return render(request, 'tickets/partials/ticket_detail.html', {
#         'ticket': ticket,
#         'updates': updates,
#         'messages': messages,
#     })
