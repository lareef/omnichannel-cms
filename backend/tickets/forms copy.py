from django import forms
from .models import Ticket, TicketUpdate, Message, EscalationPolicy, TicketStatus, TicketPriority
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout, Field

class TicketFilterForm(forms.Form):
    ASSIGNMENT_CHOICES = [
        ('', 'All'),
        ('assigned_to_me', 'Assigned to me'),
        ('unassigned', 'Unassigned'),
    ]

    status = forms.ModelChoiceField(queryset=TicketStatus.objects.all(), required=False, empty_label="All")
    priority = forms.ModelChoiceField(queryset=TicketPriority.objects.all(), required=False, empty_label="All")
    assignment = forms.ChoiceField(choices=ASSIGNMENT_CHOICES, required=False)
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search ticket # or subject'}))

    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset', None)
        self.user = None
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False                     # we'll keep the outer <form> in the template
        self.helper.disable_csrf = True                  # GET form doesn't need CSRF
        self.helper.layout = Layout(
            Field('status', css_class='mt-1 block w-full rounded-md border-blue-300 shadow-sm'),
            Field('priority', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('assignment', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('search', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
        )

    # def __init__(self, *args, queryset=None, **kwargs):
    #     super().__init__(*args, **kwargs)
        
    #     # Set choices dynamically to avoid database queries at import time
    #     try:
    #         status_choices = [('', 'All')] + list(Ticket.objects.values_list('status__id', 'status__name').distinct())
    #         priority_choices = [('', 'All')] + list(Ticket.objects.values_list('priority__id', 'priority__name').distinct())
            
    #         self.fields['status'].choices = status_choices
    #         self.fields['priority'].choices = priority_choices
    #     except:
    #         # Fallback if database is not ready (e.g., during migrations)
    #         self.fields['status'].choices = [('', 'All')]
    #         self.fields['priority'].choices = [('', 'All')]
        
    #     if queryset:
    #         # Dynamically set choices based on queryset (optional)
    #         pass

    # def __init__(self, *args, **kwargs):
    #     queryset = kwargs.pop('queryset', None)
    #     super().__init__(*args, **kwargs)
    #     if queryset:
    #         # ✅ Correct: get unique statuses
    #         status_choices = [('', 'All')] + list(
    #             queryset.order_by('status__name')
    #                 .values_list('status__id', 'status__name')
    #                 .distinct()
    #         )
    #         self.fields['status'].choices = status_choices

    #         priority_choices = [('', 'All')] + list(
    #             queryset.order_by('priority__level')
    #                 .values_list('priority__id', 'priority__name')
    #                 .distinct()
    #         )
    #         self.fields['priority'].choices = priority_choices


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
        
    def get_queryset(self):
        # Start with the base queryset
        queryset = Ticket.objects.select_related(
            'status', 'priority', 'customer', 'assigned_to'
        ).order_by('-created_at')

        user = self.request.user

        # Role‑based filtering (agents vs supervisors)
        if user.role and user.role.code == 'agent':
            queryset = queryset.filter(
                Q(assigned_to=user) |
                Q(assigned_to__isnull=True, department=user.department)
            )

        # ---- STAT CARD FILTERS (custom parameters) ----
        # Open tickets
        if self.request.GET.get('open') == '1':
            queryset = queryset.filter(status__is_closed_state=False)

        # Overdue response
        if self.request.GET.get('overdue_response') == '1':
            now = timezone.now()
            queryset = queryset.filter(
                response_due_at__lt=now,
                first_response_at__isnull=True
            )
        # -------------------------------------------------

        # Now apply the standard filter form (which handles assignment, status, priority, search)
        self.filter_form = TicketFilterForm(self.request.GET, queryset=queryset)
        self.filter_form.set_user(user)

        if self.filter_form.is_valid():
            queryset = self.filter_form.filter_queryset(queryset)

        # Store the final filtered queryset for stats
        self.filtered_queryset = queryset
        return queryset

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
        return ticket, changes  # return changes for notification logic in view
    
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Send', css_class='bg-indigo-600 text-white'))
    class Meta:
        model = Message
        fields = ['content', 'is_internal_note']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Type your message...'}),
        }

class EscalationPolicyForm(forms.ModelForm):
    class Meta:
        model = EscalationPolicy
        fields = ['name', 'description', 'trigger_event', 'threshold_minutes',
                  'level', 'escalate_to_role', 'escalate_to_user', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Field('name', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('description', rows=3, css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('trigger_event', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('threshold_minutes', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('level', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('escalate_to_role', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('escalate_to_user', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('is_active'),
            Submit('submit', 'Save Policy', css_class='bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700')
        )
