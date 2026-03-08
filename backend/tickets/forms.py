from django import forms
from .models import Ticket, TicketUpdate, Message
from django.db.models import Q


class TicketFilterForm(forms.Form):
    ASSIGNMENT_CHOICES = [
        ('', 'All'),
        ('assigned_to_me', 'Assigned to me'),
        ('unassigned', 'Unassigned'),
    ]

    status = forms.ChoiceField(required=False)
    priority = forms.ChoiceField(required=False)
    assignment = forms.ChoiceField(choices=ASSIGNMENT_CHOICES, required=False)
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search ticket # or subject'}))

    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set choices dynamically to avoid database queries at import time
        try:
            status_choices = [('', 'All')] + list(Ticket.objects.values_list('status__id', 'status__name').distinct())
            priority_choices = [('', 'All')] + list(Ticket.objects.values_list('priority__id', 'priority__name').distinct())
            
            self.fields['status'].choices = status_choices
            self.fields['priority'].choices = priority_choices
        except:
            # Fallback if database is not ready (e.g., during migrations)
            self.fields['status'].choices = [('', 'All')]
            self.fields['priority'].choices = [('', 'All')]
        
        if queryset:
            # Dynamically set choices based on queryset (optional)
            pass

    def filter_queryset(self, queryset):
        data = self.cleaned_data
        if data.get('status'):
            queryset = queryset.filter(status_id=data['status'])
        if data.get('priority'):
            queryset = queryset.filter(priority_id=data['priority'])
        if data.get('assignment') == 'assigned_to_me':
            queryset = queryset.filter(assigned_to=self.user)  # need to set user
        elif data.get('assignment') == 'unassigned':
            queryset = queryset.filter(assigned_to__isnull=True)
        if data.get('search'):
            queryset = queryset.filter(
                Q(ticket_number__icontains=data['search']) |
                Q(subject__icontains=data['search']) |
                Q(customer_name__icontains=data['search'])
            )
        return queryset

    def set_user(self, user):
        self.user = user

class TicketUpdateForm(forms.ModelForm):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Add a comment...'}),
        required=False
    )

    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'assigned_to']

    def __init__(self, *args, **kwargs):
        # Pop the current user from kwargs (passed from view)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Restrict assignable users based on role
        if self.user and self.user.role:
            if self.user.role.code == 'agent':
                # Agents can only assign to themselves or leave unassigned
                self.fields['assigned_to'].queryset = self.user.__class__.objects.filter(id=self.user.id)
                self.fields['assigned_to'].empty_label = "Unassigned"
            elif self.user.role.code in ['supervisor', 'admin']:
                # Supervisors/admins can assign anyone in the same department (or all)
                # Adjust as needed: here we allow all users in the same department
                self.fields['assigned_to'].queryset = self.user.__class__.objects.filter(
                    department=self.user.department, is_active=True
                )
                self.fields['assigned_to'].empty_label = "Unassigned"
        # If no user, show empty queryset (shouldn't happen)

        # Store original values to detect changes
        if self.instance.pk:
            self.original_status = self.instance.status
            self.original_priority = self.instance.priority
            self.original_assigned_to = self.instance.assigned_to

    def save(self, updated_by=None, commit=True):
        ticket = super().save(commit=False)
        if commit:
            changes = {}
            if self.original_status != ticket.status:
                changes['old_status'] = self.original_status
                changes['new_status'] = ticket.status
            if self.original_priority != ticket.priority:
                changes['old_priority'] = self.original_priority
                changes['new_priority'] = ticket.priority
            if self.original_assigned_to != ticket.assigned_to:
                changes['old_assigned_to'] = self.original_assigned_to
                changes['new_assigned_to'] = ticket.assigned_to
            ticket.save()
            if changes or self.cleaned_data.get('comment'):
                TicketUpdate.objects.create(
                    ticket=ticket,
                    updated_by=updated_by,
                    update_type='other' if changes else 'comment',
                    comment=self.cleaned_data.get('comment', ''),
                    **changes
                )
        return ticket
    
class old_TicketUpdateForm(forms.ModelForm):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Add a comment...'}),
        required=False
    )

    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'assigned_to']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store original values to detect changes
        if self.instance.pk:
            self.original_status = self.instance.status
            self.original_priority = self.instance.priority
            self.original_assigned_to = self.instance.assigned_to

    def save(self, updated_by=None, commit=True):
        ticket = super().save(commit=False)
        if commit:
            changes = {}
            if self.original_status != ticket.status:
                changes['old_status'] = self.original_status
                changes['new_status'] = ticket.status
            if self.original_priority != ticket.priority:
                changes['old_priority'] = self.original_priority
                changes['new_priority'] = ticket.priority
            if self.original_assigned_to != ticket.assigned_to:
                changes['old_assigned_to'] = self.original_assigned_to
                changes['new_assigned_to'] = ticket.assigned_to
            ticket.save()
            if changes or self.cleaned_data.get('comment'):
                TicketUpdate.objects.create(
                    ticket=ticket,
                    updated_by=updated_by,
                    update_type='other' if changes else 'comment',
                    comment=self.cleaned_data.get('comment', ''),
                    **changes
                )
        return ticket


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'is_internal_note']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Type your message...'}),
        }