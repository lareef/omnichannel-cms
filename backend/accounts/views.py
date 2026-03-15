from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from tickets.views import SupervisorRequiredMixin  # adjust import as needed
from .models import User
from .services import activate_users


class PendingUserListView(LoginRequiredMixin, SupervisorRequiredMixin, ListView):
    """List all inactive users for supervisor approval."""
    model = User
    template_name = 'accounts/pending_users.html'
    context_object_name = 'users'
    queryset = User.objects.filter(is_active=False).order_by('date_joined')


@require_POST
def activate_user(request, pk):
    """Activate a single user."""
    user = get_object_or_404(User, pk=pk)
    activate_users(User.objects.filter(pk=pk))
    messages.success(request, f"User {user.username} has been activated.")
    return redirect('accounts:pending_users')


@require_POST
def bulk_activate_users(request):
    """Activate multiple users selected via checkboxes."""
    user_ids = request.POST.getlist('user_ids')
    if user_ids:
        queryset = User.objects.filter(pk__in=user_ids)
        count = activate_users(queryset)
        messages.success(request, f"{count} user(s) activated.")
    else:
        messages.warning(request, "No users selected.")
    return redirect('accounts:pending_users')
# Create your views here.
