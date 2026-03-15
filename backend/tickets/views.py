from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Ticket, TicketUpdate, Message, MessageAttachment
from .forms import TicketFilterForm, TicketUpdateForm, MessageForm
from django.http import HttpResponseForbidden, HttpResponse
from accounts.decorators import role_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, View
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils import timezone
from notifications.utils import notify_ticket_update
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

# ----- Mixins for Role-Based Access -----
# class AgentRequiredMixin(UserPassesTestMixin):
#     """Allow only agents, supervisors, and admins."""
#     def test_func(self):
#         user = self.request.user
#         if not user.is_authenticated:
#             return False
#         # Assuming role codes: 'agent', 'supervisor', 'admin'
#         return user.role and user.role.code in ['agent', 'supervisor', 'admin']

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
        return user.is_authenticated and user.role and user.role.code in ['supervisor', 'admin']

# ----- Dashboard / Ticket List -----
class DashboardView(LoginRequiredMixin, AgentRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/dashboard.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        queryset = Ticket.objects.select_related(
            'status', 'priority', 'customer', 'assigned_to'
        ).order_by('-created_at')
        
        # self.filter_form.set_user(user)  # Pass user to filter form for assignment filtering

        # Filter by user role
        user = self.request.user
        if user.role and user.role.code == 'agent':
            # Agents see only tickets assigned to them or unassigned tickets in their department
            queryset = queryset.filter(
                Q(assigned_to=user) |
                Q(assigned_to__isnull=True, department=user.department)
            )
        # Supervisors and admins see all

        # Apply request filters
        self.filter_form = TicketFilterForm(self.request.GET, queryset=queryset)

        # IMPORTANT: give the form the current user
        self.filter_form.set_user(user)

        if self.filter_form.is_valid():
            queryset = self.filter_form.filter_queryset(queryset)
        return queryset

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['filter_form'] = self.filter_form
    #     return context

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            user = self.request.user
            base_qs = Ticket.objects.all()

            # Counts for stats cards
            context['open_tickets_count'] = base_qs.filter(status__is_closed_state=False).count()
            context['unassigned_count'] = base_qs.filter(assigned_to__isnull=True).count()
            context['overdue_response_count'] = base_qs.filter(
                response_due_at__lt=timezone.now(),
                first_response_at__isnull=True
            ).count()
            context['my_tickets_count'] = base_qs.filter(assigned_to=user).count()

            context['filter_form'] = self.filter_form
            return context
# Simple ticket list view (same as dashboard but without the dashboard-specific UI)
class TicketListView(DashboardView):
    template_name = 'tickets/partials/ticket_list.html'


# ----- Ticket Detail -----
class TicketDetailView(LoginRequiredMixin, AgentRequiredMixin, DetailView):
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

def update_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    # Permission check (as before)
    user = request.user
    if user.role and user.role.code == 'agent' and not (ticket.assigned_to == user or (ticket.assigned_to is None and ticket.department == user.department)):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = TicketUpdateForm(request.POST, instance=ticket, user=user)  # pass user
        if form.is_valid():
            ticket, changes = form.save(updated_by=user)
            # Create notifications
            if changes:
                notify_ticket_update(ticket, changes, updated_by=request.user)
            messages.success(request, "Ticket updated successfully.")
            # Return updated detail partial
            messages_qs = ticket.messages.select_related('sender_user').prefetch_related('attachments').order_by('sent_at')
            context = {
                'ticket': ticket,
                'messages': messages_qs,
            }
            html = render_to_string('tickets/partials/ticket_detail.html', context, request=request)
            # return HttpResponse(html)
            response = HttpResponse(html)
            response['HX-Trigger'] = '{"showToast": {"message": "Ticket updated successfully", "type": "success"}}'
            return response
        else:
            html = render_to_string('tickets/partials/update_form.html', {'form': form, 'ticket': ticket}, request=request)
            return HttpResponse(html, status=400)
    else:
        form = TicketUpdateForm(instance=ticket, user=user)  # pass user
        return render(request, 'tickets/partials/update_form.html', {'form': form, 'ticket': ticket})
    
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
